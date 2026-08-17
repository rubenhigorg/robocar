#!/bin/bash


source /opt/ros/humble/setup.bash
source /home/lab/robocar/src/install/setup.sh
source /home/lab/robocar/.venv/bin/activate

# bash /home/lab/robocar/nodered.sh &
ros2 launch teleop_twist_joy teleop-launch.py &
ros2 run robocar_pkg car_control_node &
ros2 run robocar_pkg energy_node & 
ros2 run robocar_pkg accelerometer_node & 
ros2 run robocar_pkg encoder_node --ros-args -p pulses_per_rev:=143.8 -p wheel_diameter_m:=0.068 -p publish_rate_hz:=30.0 & 
ros2 run robocar_pkg distance_node 
# ros2 run robocar_pkg camera_node
