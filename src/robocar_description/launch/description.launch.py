"""Publica el modelo del Robocar y su arbol TF (robot_state_publisher).

Uso:
    ros2 launch robocar_description description.launch.py

Con foxglove_bridge corriendo, el panel 3D de Foxglove mostrara el coche.
"""
import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('robocar_description')
    xacro_file = os.path.join(pkg, 'urdf', 'robocar.urdf.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
    ])
