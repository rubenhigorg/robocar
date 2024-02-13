import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from adafruit_servokit import ServoKit

class MotorNode(Node):

    def __init__(self):
        super().__init__('motor_node')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.kit = ServoKit(channels=16)

    def listener_callback(self, msg):
        # Aquí puedes añadir el código para controlar los motores con self.kit
        # Por ejemplo:
        self.kit.servo[0].angle = msg.linear.x * 10
        # self.kit.servo[1].angle = msg.angular_z

def main(args=None):
    rclpy.init(args=args)

    motor_node = MotorNode()

    rclpy.spin(motor_node)

    motor_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()