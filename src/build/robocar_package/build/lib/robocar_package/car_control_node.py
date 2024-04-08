from os import wait
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from adafruit_servokit import ServoKit

class CarControlNode(Node):

    def __init__(self):
        super().__init__('car_control_node')
        self.subscription_joy = self.create_subscription(
            Joy,
            'joy',
            self.listener_callback_motor,
            10)
        self.kit = ServoKit(channels=16)


    def listener_callback_motor(self, msg):
        # Mapear la velocidad angular a la dirección
        angleDir = self.map_value_direction(msg.axes[0], 1.0, -1.0, 170.0, 40.0)
        self.get_logger().info('Dir: %s' % angleDir)
        self.kit.servo[2].angle = angleDir

        if msg.buttons[4] == 1: # Si esta pulsado L1 ira marcha atras:
            angleMotor = self.map_value_motor(msg.axes[5], 0.9999, -0.9999, 55, 80) * 1.8  # msg.axes[5] = R2 potenciometro    
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

def main(args=None):
    rclpy.init(args=args)
    control_node = CarControlNode()
    rclpy.spin(control_node)
    control_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()