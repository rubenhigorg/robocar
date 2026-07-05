import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ekf_config = os.path.join(
        get_package_share_directory('robocar_pkg'), 'config', 'ekf.yaml')

    return LaunchDescription([
        # Adaptador: /wheel_speed (TwistStamped) -> /wheel_speed_cov (con covarianza)
        Node(
            package='robocar_pkg',
            executable='wheel_twistcov_node',
            name='wheel_twistcov_node',
            output='screen',
        ),
        # EKF: fusiona encoder (vx) + IMU (yaw rate) -> odom -> base_link
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
        ),
    ])
