import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ekf_config = os.path.join(
        get_package_share_directory('robocar_pkg'), 'config', 'ekf.yaml')

    # NOTA CPU (2026-08-31): ELIMINADOS del arranque para aliviar la Pi4:
    #  - rf2o_laser_odometry + odom_cov_node (estaban DESACTIVADOS en el EKF,
    #    odom0 comentado, pero hacian scan-matching ~20-25% CPU).
    #  - steer_yaw_node (twist1 del EKF): entrada de yaw de BAJA confianza
    #    (yaw_variance 0.5 en suelo -> apenas pesaba; la IMU manda el rumbo) y
    #    costaba ~17% CPU. El EKF queda con encoder(vx) + IMU(yaw). ekf.yaml
    #    aun define twist1=steer_yaw_cov pero como nadie lo publica, no se fusiona.
    #  Para reactivar cualquiera, volver a lanzar su Node aqui.
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
