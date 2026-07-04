import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from messages_pkg.msg import Distance
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

        GPIO.setmode(GPIO.BCM)

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

        pulse_end = pulse_start
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end - pulse_start > 0.03:
                return -1.0  # eco atascado en alto

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
        msg.emergency_stop = bool(GPIO.input(6)) # emergency_stop
        self.get_logger().info(f'Publishing: {msg}')
        self.publisher_.publish(msg)

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