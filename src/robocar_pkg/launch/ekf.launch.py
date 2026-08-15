import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ekf_config = os.path.join(
        get_package_share_directory('robocar_pkg'), 'config', 'ekf.yaml')

    return LaunchDescription([
        # Odometria laser: scan-matching del LIDAR -> /odom_rf2o.
        # publish_tf=False: el EKF es el dueno de odom->base_link, rf2o NO lo publica.
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/odom_rf2o',
                'publish_tf': False,
                'base_frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'init_pose_from_topic': '',   # '' -> arranca en 0; SIN esto ignora los scans
                'freq': 10.0,
            }],
        ),
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
