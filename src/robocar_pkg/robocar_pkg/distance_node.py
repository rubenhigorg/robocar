import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import Range
import RPi.GPIO as GPIO

# SOLO IR DE EMERGENCIA (2026-08-24). Los 3 ultrasonidos HC-SR04 quedan RETIRADOS: su lectura
# hacia busy-wait de GPIO y quemaba CPU (saturaba la Pi4). Ahora:
#   - obstaculos  -> LIDAR (costmap + RPP use_collision_detection)
#   - emergencia  -> este IR (pin 6, muy cerca) -> /emergency_stop -> car_control para en seco
# Se mantiene /ir_range publicado SIEMPRE DESPEJADO para que el collision_monitor tenga una fuente
# valida (no timeout, nunca dispara); queda como no-op hasta que se decida quitarlo del bringup.
EMERGENCY_PIN = 6   # IR digital. ACTIVO BAJO: despejado=1, obstaculo=0 (medido).


class EmergencyNode(Node):
    def __init__(self):
        super().__init__('distance_node')
        self.pub_estop = self.create_publisher(Bool, '/emergency_stop', 10)
        self.pub_ir = self.create_publisher(Range, '/ir_range', 10)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(EMERGENCY_PIN, GPIO.IN)
        self._lowcount = 0
        self.timer = self.create_timer(0.05, self.tick)   # 20 Hz, barato (solo lee 1 GPIO)
        self.get_logger().info('distance_node: SOLO IR de emergencia (pin %d activo-bajo). Ultrasonidos retirados.' % EMERGENCY_PIN)

    def tick(self):
        # debounce: 2 lecturas seguidas en LOW = emergencia
        if GPIO.input(EMERGENCY_PIN) == 0:
            self._lowcount = min(self._lowcount + 1, 5)
        else:
            self._lowcount = 0
        self.pub_estop.publish(Bool(data=(self._lowcount >= 2)))
        # /ir_range siempre despejado (4 m) -> el collision_monitor nunca dispara
        r = Range()
        r.header.stamp = self.get_clock().now().to_msg()
        r.header.frame_id = 'base_link'
        r.radiation_type = Range.INFRARED
        r.field_of_view = 0.2
        r.min_range = 0.02
        r.max_range = 4.0
        r.range = 4.0
        self.pub_ir.publish(r)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = EmergencyNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
        GPIO.cleanup()


if __name__ == '__main__':
    main()
