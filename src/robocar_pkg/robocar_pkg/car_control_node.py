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
        # STALL-BREAKER: si comando avanzar pero el encoder dice que NO me muevo, subo el gas
        # gradualmente hasta que arranca (rompe el rozamiento estatico; se adapta a suelo/bateria).
        self.declare_parameter('stall_boost_max', 14.0)   # grados extra de gas maximos
        self.declare_parameter('stall_speed_eps', 0.03)   # m/s por debajo = "parado"

        self.kit = ServoKit(channels=16)
        self.autonomous_mode = self.get_parameter('autonomous_start').value
        self.meas_speed = 0.0     # velocidad real (encoder/EKF) para el stall-breaker
        self.stall_boost = 0.0
        self.create_subscription(Odometry, '/odometry/filtered', self._odom_cb, 10)
        self.create_subscription(Bool, '/set_autonomous', self._set_auto_cb, 10)  # armar/desarmar desde la web
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
        # Puente Ackermann: /cmd_vel (Twist) -> servo direccion + ESC.
        # Solo actua en modo autonomo (igual que lane_info).
        if not self.autonomous_mode:
            return

        self.last_cmd_vel_time = self.get_clock().now()
        max_ang = self.get_parameter('max_angular').value
        steer_center = self.get_parameter('steer_center').value
        steer_span = self.get_parameter('steer_span').value
        max_lin = self.get_parameter('max_linear').value
        stop = self.get_parameter('throttle_stop').value
        start = self.get_parameter('throttle_start').value
        full = self.get_parameter('throttle_full').value

        # Direccion: angular.z (rad/s) -> canal 2. angular.z > 0 (giro a la izq) -> servo > centro.
        ang = msg.angular.z
        steer = steer_center + (ang / max_ang) * steer_span if max_ang else steer_center
        steer = self.clamp(steer, 40.0, 170.0)
        self.kit.servo[2].angle = float(steer)

        # Traccion: linear.x (m/s) -> canales 0 y 1. ESC bidireccional (verificado):
        # ADELANTE = bajar el angulo desde el neutro (93.6 -> 27); ATRAS = subir
        # el angulo (93.6 -> ~108).
        lin = msg.linear.x
        rev_start = self.get_parameter('throttle_rev_start').value
        rev_full = self.get_parameter('throttle_rev_full').value
        max_lin_rev = self.get_parameter('max_linear_rev').value
        if max_lin <= 0.0:
            throttle = stop
        elif lin > 0.0:
            frac = min(lin / max_lin, 1.0)
            throttle = start - frac * (start - full)
            throttle = self.clamp(throttle, self.THROTTLE_HARD_FLOOR, stop)
        elif lin < 0.0:
            frac = min(-lin / max_lin_rev, 1.0)
            throttle = rev_start + frac * (rev_full - rev_start)
            throttle = self.clamp(throttle, stop, self.THROTTLE_HARD_CEIL)
        else:
            throttle = stop
        # STALL-BREAKER: si comando AVANZAR pero el encoder dice que NO me muevo, subo el gas
        # progresivamente hasta que arranca; cuando ya rueda, aflojo. (idea de Ruben: el robot
        # sabe si se mueve -> cerrar el lazo en el arranque, rompe el rozamiento estatico del suelo).
        eps = self.get_parameter('stall_speed_eps').value
        if lin > 0.02:
            if abs(self.meas_speed) < eps:
                self.stall_boost = min(self.stall_boost + 0.4, self.get_parameter('stall_boost_max').value)
            else:
                self.stall_boost = max(self.stall_boost - 0.6, 0.0)
            throttle = self.clamp(throttle - self.stall_boost, self.THROTTLE_HARD_FLOOR, stop)  # bajar angulo = mas gas
        else:
            self.stall_boost = 0.0
        # Rampa anti-pico: DAR gas (alejarse del neutro, en cualquier sentido) se
        # limita a max_throttle_step por comando; QUITAR gas (hacia el neutro) es
        # instantaneo (freno inmediato).
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
            'cmd_vel -> steer=%.1f throttle=%.1f (lin=%.2f ang=%.2f)'
            % (steer, throttle, msg.linear.x, ang))

    def _odom_cb(self, msg):
        self.meas_speed = msg.twist.twist.linear.x   # velocidad real para el stall-breaker

    def _set_auto_cb(self, msg):
        self.autonomous_mode = bool(msg.data)
        self.get_logger().info('autonomous_mode = %s (via /set_autonomous)' % self.autonomous_mode)
        if not self.autonomous_mode:
            self.stall_boost = 0.0
            self.set_throttle_neutral()

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