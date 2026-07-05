"""SLAM 2D del Robocar: Cartographer + publicador del mapa de ocupacion.

Requiere: TF del modelo (description.launch.py) y /scan (rplidar) ya corriendo
— launch-panel.sh levanta ambos.

    ros2 launch robocar_slam slam.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_dir = os.path.join(get_package_share_directory('robocar_slam'), 'config')

    return LaunchDescription([
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            arguments=[
                '-configuration_directory', config_dir,
                '-configuration_basename', 'robocar_2d.lua',
            ],
            remappings=[('scan', '/scan')],
        ),
        # Convierte los submaps en /map (nav_msgs/OccupancyGrid) para Nav2 y el panel
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='occupancy_grid_node',
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0'],
        ),
    ])
