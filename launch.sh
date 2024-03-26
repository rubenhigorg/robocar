#!/bin/bash

source /home/lab/robocar/install/setup.sh
ros2 launch teleop_twist_joy teleop-launch.py &
ros2 run robocar_package robocar_node
