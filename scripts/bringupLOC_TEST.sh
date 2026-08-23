#!/bin/bash
# FASE 1 (prueba de alineacion): Cartographer PURE-LOCALIZATION sobre un .pbstream + puente TF->/amcl_pose.
# Objetivo unico: que el laser quede ALINEADO y ESTABLE con el mapa en el panel, SIN Nav2 todavia.
# Uso: bash bringupLOC_TEST.sh [ruta.pbstream]   (por defecto el checkpoint mas reciente)
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1
PB="${1:-$(ls -t ~/robocar/maps/checkpoints/ckpt_*.pbstream 2>/dev/null | head -1)}"
[ -f "$PB" ] || { echo "ERROR: no existe pbstream: $PB"; exit 1; }
echo "  Cartographer-localization contra: $PB"

bash ~/robocar/scripts/stopall.sh; sleep 2
L=~/robocar/logs; mkdir -p "$L"
run(){ local name="$1"; shift; echo "  -> $name"; nohup "$@" >"$L/$name.log" 2>&1 & disown; }

run description ros2 launch robocar_description description.launch.py; sleep 2
run rplidar ros2 run rplidar_ros rplidar_node --ros-args \
              -p serial_port:=/dev/serial0 -p serial_baudrate:=460800 \
              -p frame_id:=laser -p scan_mode:=Standard -p angle_compensate:=true
run encoder ros2 run robocar_pkg encoder_node
run imu     ros2 run robocar_pkg accelerometer_node
sleep 2
run ekf ros2 launch robocar_pkg ekf.launch.py; sleep 3
# Cartographer en PURE-LOCALIZATION: carga el pbstream congelado + config localization.
export SLAM_LOAD_STATE="$PB"
export SLAM_CONFIG="robocar_2d_localization.lua"
run slam ros2 launch robocar_slam slam.launch.py
echo "  -> (cartographer localizando, ~8-15 s para enganchar)"
sleep 4
# Puente TF map->base_link -> /amcl_pose (para el panel, sin tocarlo)
run pose_bridge python3 ~/robocar/src/robocar_pkg/robocar_pkg/tf_to_amclpose.py
run health      python3 ~/robocar/src/robocar_pkg/robocar_pkg/robocar_health_node.py
run rosbridge   ros2 launch rosbridge_server rosbridge_websocket_launch.xml
sleep 2
echo ""
echo "LOC TEST listo. Abre trayectorias.html (Ctrl+Shift+R): el laser debe encajar con el mapa y NO derivar."
