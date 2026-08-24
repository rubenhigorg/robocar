import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from messages_pkg.msg import Distance
from sensor_msgs.msg import Range   # puente al contrato de nav2 (igual que sim_sensors)
import RPi.GPIO as GPIO
import time

# Define los pines de los sensores

# IZQUIERDA (verde)
TRIG1 = 19  # Define tu pin TRIG para el sensor 1
ECHO1 = 16  # Define tu pin ECHO para el sensor 1

# DERECHA (amarillo)
TRIG2 = 26  # Define tu pin TRIG para el sensor 2
ECHO2 = 20  # Define tu pin ECHO para el sensor 2

# CENTRO (rojo)
TRIG3 = 12  # Define tu pin TRIG para el sensor 3
ECHO3 = 13  # Define tu pin ECHO para el sensor 3

class UltrasoundNode(Node):
    def __init__(self):
        super().__init__('distance_node')
        self.publisher_ = self.create_publisher(Distance, 'ultrasound_data', 10)
        self.timer = self.create_timer(0.1, self.talker)  # 10Hz

        # --- PUENTE al contrato de nav2 (identico a sim_sensors): ultrasonidos como
        #     sensor_msgs/Range para la range_layer del costmap (EVITACION) + /ir_range =
        #     proximidad FRONTAL (ultrasonido central, capada a 0.5 m) para el
        #     collision_monitor (PARADA). Frames segun el URDF (robot_state_publisher). ---
        self.US_MAX = 3.0    # m (alcance ultrasonidos)
        self.IR_MAX = 0.5    # m (proximidad frontal para la parada)
        self.us_frames = {'center': 'ultrasound_center',
                          'left': 'ultrasound_left', 'right': 'ultrasound_right'}
        self.pub_us_range = {k: self.create_publisher(Range, '/us_' + k, 10) for k in self.us_frames}
        self.pub_ir = self.create_publisher(Range, '/ir_range', 10)
        # IR de emergencia (pin 6): parada dura anti-empujar-pared (~2 cm). ACTIVO BAJO
        # (medido 2026-08-24: despejado GPIO6=1, obstaculo=0). Con debounce anti-glitch.
        self.pub_estop = self.create_publisher(Bool, '/emergency_stop', 10)
        self._em_lowcount = 0
        # filtro de mediana (ventana 5) anti-espurios: los HC-SR04 dan picos cortos (8cm, 81cm...)
        # intermitentes que hacian frenar en falso al collision_monitor por /ir_range.
        self._hist = {'center': [], 'left': [], 'right': []}

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(TRIG1, GPIO.OUT)
        GPIO.setup(ECHO1, GPIO.IN)

        GPIO.setup(TRIG2, GPIO.OUT)
        GPIO.setup(ECHO2, GPIO.IN)

        GPIO.setup(TRIG3, GPIO.OUT)
        GPIO.setup(ECHO3, GPIO.IN)

        GPIO.setup(6, GPIO.IN)

    def get_distance(self, TRIG, ECHO):
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        # Timeouts: un HC-SR04 sano responde en <25ms (rango 4m). Sin esto,
        # un sensor con cableado flojo cuelga el nodo para siempre (jul 2026).
        t0 = time.time()
        pulse_start = t0
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if pulse_start - t0 > 0.03:
                return -1.0  # sin eco: sensor mudo/desconectado
            time.sleep(0.0001)   # CEDER CPU: sin esto el busy-wait quema un nucleo (satura la Pi -> rosbridge cae)

        pulse_end = pulse_start
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end - pulse_start > 0.03:
                return -1.0  # eco atascado en alto
            time.sleep(0.0001)   # idem (resolucion ~1.7cm, sobra para evitacion)

        return round((pulse_end - pulse_start) * 17150, 2)

    def talker(self):
        left_distance = self.get_distance(TRIG1, ECHO1)
        right_distance = self.get_distance(TRIG2, ECHO2)
        center_distance = self.get_distance(TRIG3, ECHO3)
        # emergency_stop = self.get_emergency_stop()  # Asume que tienes una función que obtiene el valor del sensor de emergencia

        msg = Distance()
        msg.left_distance = left_distance
        msg.right_distance = right_distance
        msg.center_distance = center_distance
        # IR de emergencia ACTIVO BAJO: obstaculo = pin LOW. Debounce (2 lecturas seguidas) anti-glitch.
        if GPIO.input(6) == 0:
            self._em_lowcount = min(self._em_lowcount + 1, 5)
        else:
            self._em_lowcount = 0
        emergency = self._em_lowcount >= 2
        msg.emergency_stop = emergency
        self.publisher_.publish(msg)
        self.pub_estop.publish(Bool(data=emergency))

        # --- puente al contrato de nav2 (como sim_sensors), con filtro de mediana anti-espurios ---
        now = self.get_clock().now().to_msg()

        def med(key, v):
            h = self._hist[key]
            if v is not None and v > 0:          # lectura valida (ignora -1 = sin eco)
                h.append(v)
                if len(h) > 5:
                    h.pop(0)
            if not h:
                return -1.0                       # sin lecturas validas recientes -> lejos
            sh = sorted(h)
            return sh[len(sh)//2]                 # mediana: descarta picos cortos aislados
        cf = med('center', center_distance); lf = med('left', left_distance); rf = med('right', right_distance)

        def mk_range(dist_cm, frame, mx, rad, fov):
            r = Range()
            r.header.stamp = now
            r.header.frame_id = frame
            r.radiation_type = rad
            r.field_of_view = fov
            r.min_range = 0.02
            r.max_range = mx
            m = dist_cm / 100.0                                  # el sensor da cm
            r.range = float(m) if (0.0 <= m <= mx) else float(mx)  # -1 (sin eco) -> max (sin obstaculo)
            return r

        # ultrasonidos -> /us_* (Range) para la evitacion (range_layer del costmap local)
        self.pub_us_range['center'].publish(mk_range(cf, self.us_frames['center'], self.US_MAX, Range.ULTRASOUND, 0.5))
        self.pub_us_range['left'].publish(mk_range(lf,   self.us_frames['left'],   self.US_MAX, Range.ULTRASOUND, 0.5))
        self.pub_us_range['right'].publish(mk_range(rf, self.us_frames['right'],  self.US_MAX, Range.ULTRASOUND, 0.5))
        # proximidad frontal (ultrasonido central FILTRADO) -> /ir_range para el collision_monitor (parada)
        self.pub_ir.publish(mk_range(cf, 'base_link', self.IR_MAX, Range.INFRARED, 0.2))

def main(args=None):
    rclpy.init(args=args)

    try:
        ultrasound_node = UltrasoundNode()
        rclpy.spin(ultrasound_node)
    finally:
        ultrasound_node.destroy_node()
        rclpy.shutdown()
        GPIO.cleanup()

if __name__ == '__main__':
    main()