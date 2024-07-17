#!/bin/bash
source /opt/ros/iron/setup.bash
export NODE_PATH=/usr/lib/node_modules
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
source /home/lab/robocar/src/install/setup.sh
source /home/lab/robocar/src/install/setup.sh
source /home/lab/robocar/.venv/bin/activate

source setup.sh
node-red-pi --max-old-space-size=1024
