"""SLAM 2D del Robocar: Cartographer + publicador del mapa de ocupacion.

Requiere: TF del modelo (description.launch.py), /scan (rplidar) y la odometria
del EKF (/odometry/filtered, ekf.launch.py) ya corriendo.

    ros2 launch robocar_slam slam.launch.py

REANUDAR desde un checkpoint (sobrevivir a derrapes): exportar SLAM_LOAD_STATE con la
ruta a un .pbstream antes de lanzar -> Cartographer carga ese mapa y CONTINUA mapeando.
Lo hace por ti  bash ~/robocar/scripts/bringupSLAM.sh --resume-latest
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_dir = os.path.join(get_package_share_directory('robocar_slam'), 'config')

    # config seleccionable por env: robocar_2d.lua (mapeo, por defecto) o
    # robocar_2d_localization.lua (pure-localization sobre un .pbstream congelado).
    carto_args = [
        '-configuration_directory', config_dir,
        '-configuration_basename', os.environ.get('SLAM_CONFIG', 'robocar_2d.lua'),
    ]
    load_state = os.environ.get('SLAM_LOAD_STATE', '').strip()
    if load_state:
        # Carga un checkpoint y CONTINUA el mapeo (los submaps cargados quedan congelados).
        carto_args += ['-load_state_filename', load_state]
    if os.environ.get('SLAM_NO_AUTOSTART', '').strip():
        # No arranca la trayectoria sola: la lanza slam_checkpoint_node con la POSE del checkpoint
        # (start_trajectory con initial_pose) para reengancharse justo donde se guardo.
        carto_args += ['-start_trajectory_with_default_topics=false']

    return LaunchDescription([
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            arguments=carto_args,
            remappings=[('scan', '/scan'), ('odom', '/odometry/filtered')],
        ),
        # Convierte los submaps en /map (nav_msgs/OccupancyGrid) para Nav2 y el panel
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='occupancy_grid_node',
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0'],
        ),
    ])
