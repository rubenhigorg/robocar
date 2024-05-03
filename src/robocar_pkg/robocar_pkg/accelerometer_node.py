import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from lib import MPU6050
from time import sleep


class ImuPublisher(Node):

    def __init__(self):
        super().__init__('accelerometer_node')
        self.publisher_ = self.create_publisher(Imu, 'imu', 10)
        self.mpu = MPU6050.mpu6050(0x68)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        imu_msg = Imu()

        accel_data = self.mpu.get_accel_data()
        imu_msg.linear_acceleration.x = round(accel_data['x'], 2)
        imu_msg.linear_acceleration.y = round(accel_data['y'], 2)
        imu_msg.linear_acceleration.z = round(accel_data['z'], 2)

        gyro_data = self.mpu.get_gyro_data()
        imu_msg.angular_velocity.x = round(gyro_data['x'], 2)
        imu_msg.angular_velocity.y = round(gyro_data['y'], 2)
        imu_msg.angular_velocity.z = round(gyro_data['z'], 2)

        self.publisher_.publish(imu_msg)


def main(args=None):
    rclpy.init(args=args)
    imu_publisher = ImuPublisher()
    rclpy.spin(imu_publisher)
    imu_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()