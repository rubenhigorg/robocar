import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist
from collections import deque

class ControllerNode(Node):
    def __init__(self):
        super().__init__('control_node')
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'lane_info',
            self.lane_info_callback,
            10)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.kp_offset = 0.1  # Proporcional constante para el controlador
        self.kd_offset = 0.01  # Proporcional constante para el controlador

        self.kp_curvature = 0.05
        self.kd_curvature = 0.005

        self.previous_offset_error = 0.0
        self.previous_curvature_error = 0.0
        self.previous_time = self.get_clock().now()

        self.offset_window = deque(maxlen=5)
        self.curvature_window = deque(maxlen=5)

        self.previous_angular_z = 0.0
        self.max_angular_change = 0.1

        # self.timer = self.create_timer(0.1, self.publish_control)
        self.get_logger().info('Control node started')


    def lane_info_callback(self, msg):
        self.get_logger().info('Received lane info')
        objetivo_offset = -8.0
        offset = msg.data[0]
        left_radius = msg.data[1]
        right_radius = msg.data[2]

        radius = (left_radius + right_radius) / 2

        # Crear mensaje de comando
        cmd_msg = Twist()
        cmd_msg.linear.x = 0.01  # Velocidad constante hacia adelante

        cmd_msg.angular.z = radius
        self.publisher.publish(cmd_msg)



        # # Ajuste de dirección
        # if(offset < objetivo_offset - 5):
        #     # girar a la derecha pq estamos en la izqda
        #     self.get_logger().info('Girar a la derecha')
        #     cmd_msg.angular.z = -20.0
        # elif(offset > objetivo_offset + 5):
        #     # girar a la izqda pq estamos en la dcha
        #     self.get_logger().info('Girar a la izquierda')
        #     cmd_msg.angular.z = 20.0
        # else:
        #     # ir recto
        #     self.get_logger().info('Ir recto')
        #     cmd_msg.angular.z = 0.0
        # self.publisher.publish(cmd_msg)





    #     offset = msg.data[0]
    #     left_curvem = msg.data[1]
    #     right_curvem = msg.data[2]

    #     average_curvem = (left_curvem + right_curvem) / 2

    #     current_time = self.get_clock().now()
    #     dt = (current_time - self.previous_time).nanoseconds / 1e9
    #     if dt == 0:
    #         dt = 1e-9

    #     offset_error = offset
    #     curvature_error = average_curvem

    #     offset_derivative = (offset_error - self.previous_offset_error) / dt
    #     curvature_derivative = (curvature_error - self.previous_curvature_error) / dt

    #     offset_control = self.kp_offset * offset_error + self.kd_offset * offset_derivative

    #     curvature_control = self.kp_curvature * curvature_error + self.kd_curvature * curvature_derivative

    #     control_signal = offset_control + curvature_control

    #     # Crear mensaje de comando
    #     cmd_msg = Twist()
    #     cmd_msg.linear.x = 0.01  # Velocidad constante hacia adelante
    #     cmd_msg.angular.z = control_signal  # Ajuste de dirección

    #     # self.publisher.publish(cmd_msg)

    #     self.offset_window.append(offset)
    #     self.curvature_window.append(average_curvem)
    #     self.get_logger().info(f'Control signal: {control_signal}')

    # def publish_control(self):
    #     if len(self.offset_window) == 0 or len(self.curvature_window) == 0:
    #         self.get_logger().info('No data to calculate the mean') # No hay datos para calcular la media
    #         return # no hay datos para calcular la media
        
    #     smoothed_offset = sum(self.offset_window) / len(self.offset_window)
    #     smoothed_curvature = sum(self.curvature_window) / len(self.curvature_window)

    #     current_time = self.get_clock().now()
    #     dt = (current_time - self.previous_time).nanoseconds / 1e9
    #     if dt == 0:
    #         dt = 1e-9
        
    #     offset_error = smoothed_offset
    #     curvature_error = smoothed_curvature

    #     offset_derivative = (offset_error - self.previous_offset_error) / dt
    #     curvature_derivative = (curvature_error - self.previous_curvature_error) / dt

    #     offset_control = self.kp_offset * offset_error + self.kd_offset * offset_derivative
    #     curvature_control = self.kp_curvature * curvature_error + self.kd_curvature * curvature_derivative

    #     control_signal = offset_control + curvature_control

    #     angular_z = self.previous_angular_z + max(min(control_signal - self.previous_angular_z, self.max_angular_change), -self.max_angular_change)

    #     twist_msg = Twist()
    #     twist_msg.linear.x = 0.01
    #     twist_msg.angular.z = angular_z
    #     self.publisher.publish(twist_msg)
    #     self.get_logger().info(f'Control signal: {angular_z}')

    #     # Actualizar estados previos:
    #     self.previous_offset_error = offset_error
    #     self.previous_curvature_error = curvature_error
    #     self.previous_time = current_time
    #     self.previous_angular_z = angular_z


def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
