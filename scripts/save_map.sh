#!/bin/bash
# save_map.sh [nombre] - guarda el mapa que Cartographer esta construyendo.
#   1) Occupancy grid -> .pgm + .yaml  (para Nav2 y para meterlo en el simulador, Fase B)
#   2) Estado de Cartographer -> .pbstream  (para re-localizar/continuar mas tarde)
# Uso:  bash ~/robocar/scripts/save_map.sh piso_real
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1

NAME=${1:-piso_real}
DIR=~/robocar/maps
mkdir -p "$DIR"

echo "1/2  Occupancy grid  -> $DIR/$NAME.pgm / .yaml"
ros2 run nav2_map_server map_saver_cli -f "$DIR/$NAME" \
  --ros-args -p save_map_timeout:=10000.0 -p map_subscribe_transient_local:=true

echo "2/2  Estado Cartographer -> $DIR/$NAME.pbstream"
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
  "{filename: '$DIR/$NAME.pbstream', include_unfinished_submaps: true}" || \
  echo "  (si falla /write_state, el .pgm/.yaml ya vale para la Fase B)"

echo "Hecho. Mapas en $DIR/"
ls -la "$DIR"/ 2>/dev/null | grep "$NAME"
