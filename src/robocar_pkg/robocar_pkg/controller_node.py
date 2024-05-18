import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist

class ControllerNode(Node):
    def __init__(self):
        super().__init__('control_node')
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'lane_info',
            self.lane_info_callback,
            10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.kp = 1  # Proporcional constante para el controlador

    def lane_info_callback(self, msg):
        offset = msg.data[0]
        left_curvem = msg.data[1]
        right_curvem = msg.data[2]

        # Aplicar control proporcional para corregir la dirección
        control_signal = self.proportional_control(offset)

        # Crear mensaje de comando
        cmd_msg = Twist()
        cmd_msg.linear.x = 0.01  # Velocidad constante hacia adelante
        cmd_msg.angular.z = control_signal  # Ajuste de dirección

        self.publisher.publish(cmd_msg)
        self.get_logger().info(f'Control signal: {control_signal}')

    def proportional_control(self, deviation):
        control_signal = -self.kp * deviation
        return control_signal

def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
