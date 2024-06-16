import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from adafruit_servokit import ServoKit
from geometry_msgs.msg import Twist

class CarControlNode(Node):

    def __init__(self):
        super().__init__('car_control_node')
        self.subscription_joy = self.create_subscription(
            Joy,
            'joy',
            self.listener_callback_motor,
            10)
        self.subscription_cmd_vel = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
        self.kit = ServoKit(channels=16)
        self.autonomous_mode = False
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


    def cmd_vel_callback(self, msg):
        if self.autonomous_mode:
            # Convertir la velocidad angular en dirección del servo
            self.get_logger().info('cmd_vel - Angular: %s' % msg.angular.z)
            angleDir = self.map_angular_z_to_steering_angle(msg.angular.z)
            self.kit.servo[2].angle = angleDir

            # Convertir la velocidad lineal en velocidad del motor
            #angleMotor = self.map_value_motor(msg.linear.x, 0, 1, 51, 15) * 1.8
            angleMotor = self.map_value_motor(0.01, 0, 1, 51, 15) * 1.8

            self.get_logger().info('cmd_vel - Motor 0: %s' % angleMotor)
            self.kit.servo[0].angle = float(angleMotor)#93.0
            self.kit.servo[1].angle = float(angleMotor)#93.0
    
    
    def manual_control(self, msg):
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

    def map_angular_z_to_steering_angle(self, angular_z):
        '''
        La funcion que se aplica es la siguiente:
        f(angular_z) = -(5966/(x-105)) - 38.78

        Si por ejemplo el valor angular_z = 53, sería:
        53 = 5966/(x-105) - 38.78
        91.78 = 5966/(x-105)
        5966 = 91.78(x-105)
        5966 = 91.78x - 96.69
        6062.69 = 91.78x
        x = 66.07
        '''
        if angular_z < -53.0:
            return (105 * angular_z - 10011.1929)/(angular_z - 38.78125)
        elif -53 <= angular_z < 0:
            return 170
        elif 0 <= angular_z <= 53:
            return 40
        elif angular_z > 53:
            # Función cuadrática que tiende a 105 a medida que x aumenta
            return (105 * angular_z - 1904.0184)/(angular_z + 38.3125)

def main(args=None):
    rclpy.init(args=args)
    control_node = CarControlNode()
    rclpy.spin(control_node)
    control_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()