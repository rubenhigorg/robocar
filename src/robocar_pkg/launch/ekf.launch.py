import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ekf_config = os.path.join(
        get_package_share_directory('robocar_pkg'), 'config', 'ekf.yaml')

    # NOTA: rf2o_laser_odometry y odom_cov_node ELIMINADOS (2026-08-30). rf2o
    # estaba DESACTIVADO en el EKF (odom0 comentado en ekf.yaml) pero seguia
    # haciendo scan-matching del LIDAR -> ~20-25% de CPU tirada. La Pi iba
    # saturada (load ~7) y Nav2 fallaba por falta de CPU. Si algun dia se
    # reactiva rf2o en el EKF, hay que volver a lanzar ambos nodos.
    return LaunchDescription([
        # Adaptador: /wheel_speed (TwistStamped) -> /wheel_speed_cov (con covarianza)
        Node(
            package='robocar_pkg',
            executable='wheel_twistcov_node',
            name='wheel_twistcov_node',
            output='screen',
        ),
        # yaw_rate a partir de direccion + velocidad (entrada twist1 del EKF)
        Node(
            package='robocar_pkg',
            executable='steer_yaw_node',
            name='steer_yaw_node',
            output='screen',
            # Perfil SUELO (yaw_variance alta -> manda la IMU). BANCO: relanzar con 0.00002.
            parameters=[{'yaw_variance': 0.5}],
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
