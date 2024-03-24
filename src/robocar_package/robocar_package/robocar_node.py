from os import wait
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from adafruit_servokit import ServoKit

class MotorNode(Node):

    def __init__(self):
        super().__init__('motor_node')
        self.subscription_joy = self.create_subscription(
            Joy,
            'joy',
            self.listener_callback_motor,
            10)
        #self.subscription  # prevent unused variable warning
        self.kit = ServoKit(channels=16)
        #self.kit.servo[2].angle = 101
        #self.kit.servo[1].angle = 91

    def listener_callback_motor(self, msg):
        # Mapear la velocidad angular a la dirección
        angleDir = self.map_value_direction(msg.axes[0], 1.0, -1.0, 23.0, 180.0)
        self.get_logger().info('Dir: %s' % angleDir)
        self.kit.servo[2].angle = angleDir

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

def main(args=None):
    rclpy.init(args=args)
    motor_node = MotorNode()
    rclpy.spin(motor_node)
    motor_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()