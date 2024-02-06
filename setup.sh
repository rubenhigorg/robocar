#!/bin/bash

source /opt/ros/iron/setup.bash

# Para instalar dependencias de ROS
rosdep install --from-paths src --ignore-src -r -y
