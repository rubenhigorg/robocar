import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from adafruit_servokit import ServoKit
from std_msgs.msg import Float32MultiArray, Bool
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class CarControlNode(Node):

    # REGLA DURA (Ruben): nunca superar el 50% de gas. Rango ESC: 91.8 (reposo)
    # -> 27 (a fondo); el 50% es 59.4. Ningun parametro puede saltarse este limite.
    THROTTLE_HARD_FLOOR = 59.4
    # Tope duro simetrico para la MARCHA ATRAS (mismo 50% por encima del neutro).
    THROTTLE_HARD_CEIL = 124.0

    def __init__(self):
        super().__init__('car_control_node')
        self.subscription_joy = self.create_subscription(
            Joy,
            'joy',
            self.listener_callback_motor,
            10)
        self.subscription_lane_info = self.create_subscription(
            Float32MultiArray,
            'lane_info',
            self.lane_info_callback,
            10)
        # Nav2 / teleop hablan por /cmd_vel (Twist). Hito 0.2: puente Ackermann.
        self.subscription_cmd_vel = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)

        # Parametros de calibracion (ajustables en caliente con `ros2 param set`).
        # Rango de entrada: coincide con las escalas de teleop (0.7 m/s, 0.4 rad/s).
        # ESC BLHeli bidireccional: NEUTRO = 93.6 (1530us aprox). SOLO se arma si ve
        # senal estable en su neutro al encender (el mando lo bombardeaba a 20Hz con
        # 93.6). Adelante = BAJAR el angulo (27 = a fondo). NO cambiar throttle_stop
        # sin recalibrar el armado.
        self.declare_parameter('max_linear', 0.7)          # m/s -> throttle_full
        self.declare_parameter('max_angular', 0.4)         # rad/s -> direccion a tope
        self.declare_parameter('throttle_stop', 93.6)      # NEUTRO: para y ARMA el ESC
        self.declare_parameter('throttle_start', 90.0)     # umbral donde empieza a moverse
        self.declare_parameter('throttle_full', 78.0)      # angulo a max_linear (conservador)
        self.declare_parameter('steer_center', 105.0)      # servo direccion centrado
        self.declare_parameter('steer_span', 65.0)         # desviacion max de direccion (grados)
        self.declare_parameter('cmd_vel_timeout', 0.5)     # s sin /cmd_vel -> throttle a neutro
        self.declare_parameter('max_throttle_step', 0.5)   # grados/comando al DAR gas (rampa anti-pico)
        self.declare_parameter('throttle_rev_start', 97.0)  # umbral de reversa (angulo sobre neutro)
        self.declare_parameter('throttle_rev_full', 108.0)  # reversa a max_linear (conservador)
        self.declare_parameter('max_linear_rev', 0.5)  # m/s que mapea a throttle_rev_full (reversa mas lenta)
        # NAV_REAL arranca en autonomo (que Nav2 conduzca sin pulsar el boton X del joystick).
        self.declare_parameter('autonomous_start', False)
        # IR de emergencia (pin 6) DESACTIVADO por ahora -> se retoma despues poniendolo a True.
        self.declare_parameter('emergency_enabled', False)
        # LAZO DE VELOCIDAD (cerrado con el encoder): PI sobre la velocidad REAL (/odometry/filtered)
        # para que la velocidad medida siga a la comandada por Nav2. throttle = feed-forward (mapa
        # abierto) + correccion PI. Asi 0.12 m/s es 0.12 de verdad (antes era lazo abierto y no cuadraba).
        self.declare_parameter('closed_loop', True)       # False -> solo feed-forward (lazo abierto)
        self.declare_parameter('vel_kp', 10.0)            # grados de throttle por (m/s) de error (bajo -> sin tirones)
        self.declare_parameter('vel_ki', 6.0)             # grados por (m/s*s) (elimina el error permanente)
        self.declare_parameter('vel_i_max', 16.0)         # tope de la parte integral (grados) anti-windup
        self.declare_parameter('stall_speed_eps', 0.03)   # m/s por debajo = "parado"
        # ANTI-PATINAJE: si doy gas casi a tope y el encoder NO ve movimiento durante stall_timeout,
        # pulso NEUTRO (dejar de patinar -> odometria falsa que desubicaba a AMCL).
        self.declare_parameter('stall_timeout', 1.2)      # s
        # FRENO ACTIVO: el coche solo llega a neutro (rueda por inercia) -> rebasa los cusps y va
        # "muy rapido" en las maniobras. Se deja que el lazo entre en la zona de FRENO del ESC
        # (mandar el sentido contrario mientras rueda = freno) cuando se pasa de velocidad, y se
        # SUELTA el freno al casi pararse (para no engranar el sentido contrario sin querer).
        self.declare_parameter('brake_margin', 5.0)       # grados mas alla del neutro para frenar (0 = sin freno)
        self.declare_parameter('brake_release', 0.10)     # m/s: por debajo, soltar el freno
        # FILTRO DE DIRECCION: paso-bajo + zona muerta -> quita el temblor del volante, sobre todo
        # PARADO (el jitter de AMCL hace que RPP recalcule y mueva el servo sin que el coche avance).
        self.declare_parameter('steer_lp', 0.30)          # 0..1, menor = mas suave
        self.declare_parameter('steer_deadband', 0.8)     # grados: no mover el servo por debajo de este cambio

        self.kit = ServoKit(channels=16)
        self.autonomous_mode = self.get_parameter('autonomous_start').value
        self.meas_speed = 0.0     # velocidad real (encoder/EKF) -> lazo de velocidad
        self.vel_i = 0.0          # integrador del lazo PI de velocidad
        self.cmd_dir = 0          # sentido comandado (+1/-1/0): al cambiar, reseteo el integrador
        self.stall_ticks = 0      # ciclos comandando sin moverme (anti-patinaje/desubicacion)
        self.rev_arm = 0          # ciclos de neutro para ARMAR la reversa del ESC (dwell)
        self.steer_filt = None    # direccion filtrada (paso-bajo)
        self.steer_written = None # ultimo angulo escrito al servo (zona muerta)
        self.estop = False        # emergencia IR frontal (pin 6, activo bajo)
        self.create_subscription(Odometry, '/odometry/filtered', self._odom_cb, 10)
        self.create_subscription(Bool, '/set_autonomous', self._set_auto_cb, 10)  # armar/desarmar desde la web
        self.create_subscription(Bool, '/emergency_stop', self._estop_cb, 10)     # IR frontal: no empujar paredes
        self.current_throttle = None
        # Reposo al arrancar: para los motores y arma el ESC (necesita ver
        # senal de gas-cero un tiempo antes de aceptar comandos).
        self.set_throttle_neutral()
        # Watchdog: si el publicador de /cmd_vel muere, no dejar el throttle latcheado.
        self.last_cmd_vel_time = None
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_check)
        self.get_logger().info("CarControlNode initialized")


    def listener_callback_motor(self, msg):
        # Comprobar si el botón X (índice 0) está pulsado para cambiar de modo
        if msg.buttons[0] == 1:
            self.autonomous_mode = not self.autonomous_mode
            mode = "autonomous" if self.autonomous_mode else "manual"
            self.get_logger().info(f"Switched to {mode} mode")
            time.sleep(1)

        self.get_logger().info('Autonomous mode: %s' % self.autonomous_mode)
        if not self.autonomous_mode:
            self.manual_control(msg)


    def lane_info_callback(self, msg):
        if self.autonomous_mode:
            # Convertir la velocidad angular en dirección del servo
            self.get_logger().info('cmd_vel - Angular: %s' % msg.data[0])
            angleDir = self.map_value_direction(msg.data[0], -30.0, 30.0, 40, 170)
            self.get_logger().info('cmd_vel - Dir: %s' % angleDir)

            if angleDir > 105:
                self.get_logger().info("Going left")
            else:
                self.get_logger().info("Going right")
            self.kit.servo[2].angle = angleDir

            # Convertir la velocidad lineal en velocidad del motor
            #angleMotor = self.map_value_motor(msg.linear.x, 0, 1, 51, 15) * 1.8
            angleMotor = self.map_value_motor(0.01, 0, 1, 51, 15) * 1.8

            self.get_logger().info('cmd_vel - Motor 0: %s' % angleMotor)
            self.kit.servo[0].angle = 93.6# float(angleMotor)#93.6
            self.kit.servo[1].angle = 93.6# float(angleMotor)#93.6


    def cmd_vel_callback(self, msg):
        # Puente Ackermann + LAZO DE VELOCIDAD (PI con el encoder): /cmd_vel (Twist) -> servo + ESC.
        # Solo actua en modo autonomo (igual que lane_info).
        if not self.autonomous_mode:
            return
        # EMERGENCIA IR frontal (pin 6): NO empujar hacia delante contra un obstaculo a ~cm.
        # DESACTIVADA por ahora (emergency_enabled=False); se retoma poniendolo a True. Cuando este
        # activa: bloquea avanzar si el IR ve algo muy cerca; permite retroceder para alejarse.
        if self.get_parameter('emergency_enabled').value and self.estop and msg.linear.x >= -0.01:
            self.set_throttle_neutral()
            return

        now = self.get_clock().now()
        if self.last_cmd_vel_time is not None:
            dt = self.clamp((now - self.last_cmd_vel_time).nanoseconds / 1e9, 0.01, 0.2)
        else:
            dt = 0.05
        self.last_cmd_vel_time = now

        max_ang = self.get_parameter('max_angular').value
        steer_center = self.get_parameter('steer_center').value
        steer_span = self.get_parameter('steer_span').value
        max_lin = self.get_parameter('max_linear').value
        stop = self.get_parameter('throttle_stop').value
        start = self.get_parameter('throttle_start').value
        full = self.get_parameter('throttle_full').value
        rev_start = self.get_parameter('throttle_rev_start').value
        rev_full = self.get_parameter('throttle_rev_full').value
        max_lin_rev = self.get_parameter('max_linear_rev').value
        closed = self.get_parameter('closed_loop').value
        kp = self.get_parameter('vel_kp').value if closed else 0.0
        ki = self.get_parameter('vel_ki').value if closed else 0.0
        i_max = self.get_parameter('vel_i_max').value
        eps = self.get_parameter('stall_speed_eps').value
        stall_to = self.get_parameter('stall_timeout').value
        brake_margin = self.get_parameter('brake_margin').value
        brake_release = self.get_parameter('brake_release').value

        # Direccion: angular.z (rad/s) -> canal 2. angular.z > 0 (giro a la izq) -> servo > centro.
        # GEOMETRIA ACKERMANN: para el MISMO giro deseado (omega), el angulo de direccion se INVIERTE
        # en marcha atras -> delta = atan(L*omega/v); con v<0 cambia el signo. Sin esto, en reversa
        # el coche gira al lado equivocado y no consigue orientarse (maniobras interminables).
        ang = msg.angular.z
        lin = msg.linear.x
        meas = self.meas_speed
        # La direccion Ackermann se invierte al ir hacia ATRAS. Pero hay que invertir segun la
        # direccion REAL de movimiento (encoder), NO segun el comando: si el coche aun rueda hacia
        # delante por inercia (coasting) mientras Nav2 ya manda reversa, invertir aqui haria girar al
        # lado equivocado. Casi parado -> usar el comando (para armar bien el sentido de la reversa).
        eps_dir = self.get_parameter('stall_speed_eps').value
        reversing = (meas < 0.0) if abs(meas) > eps_dir else (lin < 0.0)
        ratio = (ang / max_ang) if max_ang else 0.0
        if reversing:
            ratio = -ratio                     # reversa: invertir la direccion
        steer = self.clamp(steer_center + ratio * steer_span, 40.0, 170.0)
        # paso-bajo + zona muerta: filtra el temblor y solo mueve el servo ante cambios reales
        lp = self.get_parameter('steer_lp').value
        db = self.get_parameter('steer_deadband').value
        self.steer_filt = steer if self.steer_filt is None else (lp * steer + (1.0 - lp) * self.steer_filt)
        if self.steer_written is None or abs(self.steer_filt - self.steer_written) > db:
            self.kit.servo[2].angle = float(self.steer_filt)
            self.steer_written = self.steer_filt

        # Traccion: linear.x (m/s) -> canales 0 y 1. ESC bidireccional: ADELANTE = BAJAR el angulo
        # desde neutro (93.6 -> 27); ATRAS = SUBIR (93.6 -> ~108). El feed-forward da el angulo base
        # segun el mapa; el PI lo corrige para que la velocidad REAL (encoder) siga a la comandada.
        if max_lin <= 0.0 or abs(lin) < 1e-3:
            throttle = stop
            self.rev_arm = 0
            self.vel_i = 0.0
            self.cmd_dir = 0
            self.stall_ticks = 0
        elif lin > 0.0:                                    # ADELANTE (mas gas = BAJAR el angulo)
            if self.cmd_dir != 1:
                self.vel_i = 0.0                           # cambio de sentido -> reset del integrador
                self.cmd_dir = 1
            self.rev_arm = 0
            frac = min(lin / max_lin, 1.0)
            ff = start - frac * (start - full)             # feed-forward (mapa abierto)
            err = lin - meas                               # v_cmd - v_real
            # freno activo: si voy hacia delante y me paso, dejar subir por encima del neutro (frena);
            # al casi pararme, no (evita engranar reversa).
            hi = stop + brake_margin if meas > brake_release else stop
            throttle = self._pi_throttle(ff, err, dt, kp, ki, i_max, -1,
                                         self.THROTTLE_HARD_FLOOR, hi)
        else:                                              # ATRAS (lin < 0; mas gas = SUBIR el angulo)
            if self.cmd_dir != -1:
                self.vel_i = 0.0
                self.cmd_dir = -1
            # QUIRK del ESC: reversa VINIENDO DE MOVERTE ADELANTE -> FRENA. Neutro un instante (arma).
            prev_t = self.current_throttle if self.current_throttle is not None else stop
            if self.rev_arm <= 0 and prev_t < stop - 0.3 and abs(meas) > 0.03:
                self.rev_arm = 8                           # ~0.4 s de neutro para armar el ESC
            if self.rev_arm > 0:
                self.rev_arm -= 1
                throttle = stop                            # neutro (arma la reversa)
                self.vel_i = 0.0                           # no integrar durante el neutro
            else:
                frac = min(-lin / max_lin_rev, 1.0)
                ff = rev_start + frac * (rev_full - rev_start)
                err = (-lin) - (-meas)                     # magnitud: v_cmd - v_real
                # freno activo en reversa: si retrocedo y me paso, dejar bajar del neutro (frena);
                # al casi pararme, no.
                lo = stop - brake_margin if meas < -brake_release else stop
                throttle = self._pi_throttle(ff, err, dt, kp, ki, i_max, +1,
                                             lo, self.THROTTLE_HARD_CEIL)

        # ANTI-PATINAJE / ANTI-DESUBICACION: si YA doy gas casi a tope y el encoder no ve movimiento
        # durante stall_timeout -> pulso NEUTRO. Evita seguir patinando (odometria falsa -> AMCL se
        # desubica) cuando el ESC no arranca (p.ej. reversa que frena). near_max mira el gas ya
        # ENTREGADO (tras rampa) para no dispararse durante el arranque normal.
        prev_actual = self.current_throttle if self.current_throttle is not None else stop
        near_max = ((lin > 0.0 and prev_actual <= self.THROTTLE_HARD_FLOOR + 2.0) or
                    (lin < 0.0 and prev_actual >= self.THROTTLE_HARD_CEIL - 2.0))
        if abs(lin) > 0.02 and abs(meas) < eps and self.rev_arm <= 0 and near_max:
            self.stall_ticks += 1
            if self.stall_ticks * dt > stall_to:
                throttle = stop
                self.vel_i = 0.0
                self.stall_ticks = 0
                self.rev_arm = 6 if lin < 0.0 else 0       # en reversa, re-arma el ESC; adelante solo respira
                self.get_logger().warn(
                    'comando %.2f m/s sin movimiento -> pulso neutro (no patinar/desubicar)' % lin)
        else:
            self.stall_ticks = 0

        # Rampa anti-pico: alejarse del neutro (dar gas) se limita a max_throttle_step por comando;
        # acercarse al neutro (quitar gas) es instantaneo (freno inmediato).
        step = self.get_parameter('max_throttle_step').value
        prev = self.current_throttle if self.current_throttle is not None else stop
        if throttle < stop:            # zona ADELANTE
            base = prev if prev < stop else stop
            throttle = max(throttle, base - step)
        elif throttle > stop:          # zona ATRAS
            base = prev if prev > stop else stop
            throttle = min(throttle, base + step)
        self.write_throttle(throttle)

        self.get_logger().info(
            'cmd_vel -> steer=%.1f thr=%.1f (cmd=%.2f real=%.2f i=%.2f)'
            % (steer, throttle, lin, meas, self.vel_i))

    def _pi_throttle(self, ff, err, dt, kp, ki, i_max, sign, lo, hi):
        # Lazo PI de velocidad. ff = feed-forward (mapa abierto); err = v_cmd - v_real (magnitud);
        # sign = -1 adelante (mas gas = BAJAR throttle), +1 reversa (mas gas = SUBIR).
        # Integrador con tope (anti-windup por clamping) -> no se dispara si satura o no arranca.
        i_lim = (i_max / ki) if ki > 1e-6 else 0.0
        self.vel_i = self.clamp(self.vel_i + err * dt, -i_lim, i_lim)
        corr = kp * err + ki * self.vel_i              # grados alejandose del neutro
        return self.clamp(ff + sign * corr, lo, hi)

    def _odom_cb(self, msg):
        self.meas_speed = msg.twist.twist.linear.x   # velocidad real para el stall-breaker

    def _set_auto_cb(self, msg):
        self.autonomous_mode = bool(msg.data)
        self.get_logger().info('autonomous_mode = %s (via /set_autonomous)' % self.autonomous_mode)
        if not self.autonomous_mode:
            self.vel_i = 0.0
            self.set_throttle_neutral()

    def _estop_cb(self, msg):
        # IR frontal (pin 6). Emergencia -> parada dura inmediata (no empujar la pared).
        was = self.estop
        self.estop = bool(msg.data)
        if self.estop and not was:
            self.set_throttle_neutral()
            self.get_logger().warn('EMERGENCIA IR frontal -> parada (permite retroceder)')

    def clamp(self, x, lo, hi):
        return max(lo, min(hi, x))

    def write_throttle(self, angle):
        # Escritura I2C con reintentos: el arranque del motor mete ruido en el bus
        # y una escritura fallida NO puede quedar silenciada (incidentes jul 2026).
        ok = True
        for ch in (0, 1):
            for attempt in range(3):
                try:
                    self.kit.servo[ch].angle = float(angle)
                    break
                except OSError as e:
                    self.get_logger().error(
                        'I2C fallo en throttle ch%d intento %d: %s' % (ch, attempt + 1, e))
                    time.sleep(0.02)
            else:
                ok = False
        if ok:
            self.current_throttle = angle
        return ok

    def set_throttle_neutral(self):
        stop = self.get_parameter('throttle_stop').value
        if not self.write_throttle(stop):
            self.get_logger().fatal('NO SE PUDO PONER EL THROTTLE A REPOSO — usar e-stop/interruptor ESC')

    def watchdog_check(self):
        # Sin /cmd_vel reciente -> neutro (una sola vez, hasta el proximo comando).
        if self.last_cmd_vel_time is None:
            return
        timeout = self.get_parameter('cmd_vel_timeout').value
        elapsed = (self.get_clock().now() - self.last_cmd_vel_time).nanoseconds / 1e9
        if elapsed > timeout:
            self.set_throttle_neutral()
            self.last_cmd_vel_time = None
            self.get_logger().warn('cmd_vel timeout (%.1fs): throttle a neutro' % timeout)


    def manual_control(self, msg):
        # Mapear la velocidad angular a la dirección
        angleDir = self.map_value_direction(msg.axes[0], 1.0, -1.0, 170.0, 40.0)
        self.get_logger().info('Dir: %s' % angleDir)
        self.kit.servo[2].angle = angleDir

        if msg.buttons[4] == 1: # Si esta pulsado L1 ira marcha atras:
            angleMotor = self.map_value_motor(0.01, 0, 1, 51, 15) * 1.8  # msg.axes[5] = R2 potenciometro    
        else:
            angleMotor = self.map_value_motor(msg.axes[5], 0.9999, -0.9999, 51, 15) * 1.8  # msg.axes[5] = R2 potenciometro

        self.get_logger().info('Motor 0: %s' % angleMotor)
        self.kit.servo[0].angle = float(angleMotor)
        self.kit.servo[1].angle = float(angleMotor)



    def map_value_direction(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def map_value_motor(self, x, in_min, in_max, out_min, out_max):
        if x > 0.98:
            return 52 # Los motores no se mueven
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def map_value(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def map_angle_to_servo_range(self, angleDir):
        # Límites del rango original (ángulo)
        minOriginal = -60
        maxOriginal = 60
        # Límites del rango destino (servo)
        minDestino = 40
        maxDestino = 170
        # Aplicar la fórmula de mapeo
        valorMapeado = (angleDir - minOriginal) * (maxDestino - minDestino) / (maxOriginal - minOriginal) + minDestino
        return valorMapeado

def main(args=None):
    rclpy.init(args=args)
    control_node = CarControlNode()
    try:
        rclpy.spin(control_node)
    except KeyboardInterrupt:
        pass
    finally:
        # Nunca dejar el throttle latcheado al salir. Si falla, que se OIGA.
        try:
            control_node.set_throttle_neutral()
        except Exception as e:
            print('FATAL: fallo poniendo throttle a reposo al salir: %s' % e, flush=True)
        control_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()