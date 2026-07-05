import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from lib import MPU6050

DEG2RAD = math.pi / 180.0


class ImuPublisher(Node):
    """Publica sensor_msgs/Imu del MPU6050 (0x68) saneado para fusion (EKF).

    - linear_acceleration en m/s^2 (el driver ya lo entrega asi).
    - angular_velocity convertida de deg/s (driver) a rad/s (convencion ROS).
    - header con timestamp y frame_id.
    - orientation NO disponible (el MPU6050 no tiene magnetometro): se marca
      orientation_covariance[0] = -1.0 segun la convencion de sensor_msgs/Imu.
    - covarianzas de gyro/accel: diagonal con varianzas parametrizables
      (defaults tipo datasheet; afinar midiendo el ruido en reposo).
    """

    def __init__(self):
        super().__init__('accelerometer_node')

        # --- Parametros ---
        self.declare_parameter('i2c_address', 0x68)
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('publish_rate_hz', 50.0)
        self.declare_parameter('angular_velocity_variance', 0.0004)    # (rad/s)^2  ~ std 0.02
        self.declare_parameter('linear_acceleration_variance', 0.01)   # (m/s^2)^2  ~ std 0.1

        addr = self.get_parameter('i2c_address').value
        self.frame_id = self.get_parameter('frame_id').value
        rate = float(self.get_parameter('publish_rate_hz').value)
        av_var = float(self.get_parameter('angular_velocity_variance').value)
        la_var = float(self.get_parameter('linear_acceleration_variance').value)

        self.mpu = MPU6050.mpu6050(addr)
        self.publisher_ = self.create_publisher(Imu, 'imu', 10)

        # Covarianzas fijas (diagonal 3x3, row-major). orientation: no disponible.
        self.orientation_cov = [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.angular_velocity_cov = [av_var, 0.0, 0.0, 0.0, av_var, 0.0, 0.0, 0.0, av_var]
        self.linear_acceleration_cov = [la_var, 0.0, 0.0, 0.0, la_var, 0.0, 0.0, 0.0, la_var]

        self.timer = self.create_timer(1.0 / rate, self.timer_callback)
        self.get_logger().info(
            'accelerometer_node listo (addr=0x%02X, frame=%s, %.0f Hz)'
            % (addr, self.frame_id, rate))

    def timer_callback(self):
        try:
            accel = self.mpu.get_accel_data()   # m/s^2
            gyro = self.mpu.get_gyro_data()     # deg/s
        except Exception as e:
            self.get_logger().warn('Error leyendo el MPU6050: %s' % e)
            return

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        msg.linear_acceleration.x = accel['x']
        msg.linear_acceleration.y = accel['y']
        msg.linear_acceleration.z = accel['z']

        msg.angular_velocity.x = gyro['x'] * DEG2RAD
        msg.angular_velocity.y = gyro['y'] * DEG2RAD
        msg.angular_velocity.z = gyro['z'] * DEG2RAD

        msg.orientation_covariance = self.orientation_cov
        msg.angular_velocity_covariance = self.angular_velocity_cov
        msg.linear_acceleration_covariance = self.linear_acceleration_cov

        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImuPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
