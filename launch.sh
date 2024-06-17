#!/bin/bash
source /home/lab/robocar/.venv/bin/activate
source /home/lab/robocar/src/install/setup.sh
ros2 launch teleop_twist_joy teleop-launch.py &
ros2 run robocar_pkg car_control_node &
ros2 run robocar_pkg energy_node & 
ros2 run robocar_pkg accelerometer_node & 
ros2 run robocar_pkg distance_node & 
ros2 run robocar_pkg camera_node
