#!/bin/bash
# bringupNAVREAL.sh - NAVEGACION REAL (Fase C) con CARTOGRAPHER-LOCALIZATION (robusto, sustituye a AMCL).
#
#   Cadena: description(TF) + RPLIDAR(/scan) + encoder + IMU + distance(US/IR) + EKF(/odometry/filtered)
#           + Cartographer-localization (pbstream congelado -> map->odom + /map) + tf_to_amclpose(/amcl_pose)
#           + Nav2 (planner/controller/behavior/bt/collision) + car_control + goal_relay/nav_config/map_areas
#           + rosbridge/health.
#   controller -> /cmd_vel_raw -> collision_monitor(IR) -> /cmd_vel -> car_control (autonomo + stall-breaker + deadman)
#
#   Localizacion = Cartographer casando el laser contra el .pbstream (65% ESTABLE; AMCL daba 28-48% y derivaba).
#   El /map sale de esos mismos submaps -> el laser encaja con el mapa por construccion.
#
# Uso: bash bringupNAVREAL.sh [ruta.pbstream]   (por defecto casa3.pbstream, o el .pbstream mas reciente)
# SEGURIDAD: primer arranque con RUEDAS AL AIRE. Parada: bash ~/robocar/scripts/estop.sh
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1
CFG=~/robocar/src/robocar_pkg/config/nav2_real.yaml
MAPS=~/robocar/maps
PB="${1:-}"
if [ -z "$PB" ]; then
  PB="$MAPS/casa3.pbstream"
  [ -f "$PB" ] || PB="$(ls -t $MAPS/*.pbstream $MAPS/checkpoints/*.pbstream 2>/dev/null | head -1)"
fi
if [ ! -f "$PB" ]; then echo "ERROR: no existe pbstream: $PB"; exit 1; fi
echo "  Localizacion (Cartographer) contra: $PB"

# pizarra limpia (mata sim/SLAM/Nav2 previos; NO al lanzador)
bash ~/robocar/scripts/stopall.sh; sleep 2
L=~/robocar/logs; mkdir -p "$L"
run(){ local name="$1"; shift; echo "  -> $name"; nohup "$@" >"$L/$name.log" 2>&1 & disown; }

# 1) TF del modelo
run description ros2 launch robocar_description description.launch.py; sleep 2
# 2) LIDAR real -> /scan
run rplidar ros2 run rplidar_ros rplidar_node --ros-args \
              -p serial_port:=/dev/serial0 -p serial_baudrate:=460800 \
              -p frame_id:=laser -p scan_mode:=Standard -p angle_compensate:=true
# 3) sensores I2C + ultrasonidos/IR (contrato nav2: /us_* evitacion, /ir_range parada)
run encoder  ros2 run robocar_pkg encoder_node
run imu      ros2 run robocar_pkg accelerometer_node
run distance python3 ~/robocar/src/robocar_pkg/robocar_pkg/distance_node.py
sleep 2
# 4) EKF -> /odometry/filtered + TF odom->base_link
run ekf ros2 launch robocar_pkg ekf.launch.py; sleep 3
# 5) LOCALIZACION: Cartographer pure-localization -> map->odom + /map (de los submaps del pbstream)
export SLAM_LOAD_STATE="$PB"
export SLAM_CONFIG="robocar_2d_localization.lua"
run slam ros2 launch robocar_slam slam.launch.py
run pose_bridge python3 ~/robocar/src/robocar_pkg/robocar_pkg/tf_to_amclpose.py   # TF map->base_link -> /amcl_pose (panel)
# ESPERAR a que Cartographer localice Y renderice TODO el /map (todos los submaps) ANTES de
# arrancar Nav2: si no, el static_layer del costmap coge un /map escaso -> sin paredes/inflado
# -> el robot roza (paso 2026-08-23). ~25 s para el render completo del pbstream.
echo "  -> (cartographer localizando + renderizando el mapa completo, ~25 s)"
sleep 25
unset SLAM_LOAD_STATE SLAM_CONFIG
# 6) Nav2 (grupo de navegacion; el mapa y map->odom los da Cartographer, NO map_server/amcl)
run planner    /opt/ros/humble/lib/nav2_planner/planner_server        --ros-args --params-file "$CFG"
run controller /opt/ros/humble/lib/nav2_controller/controller_server  --ros-args -r /cmd_vel:=/cmd_vel_raw --params-file "$CFG"
run behavior   /opt/ros/humble/lib/nav2_behaviors/behavior_server     --ros-args --params-file "$CFG"
run bt_navigator /opt/ros/humble/lib/nav2_bt_navigator/bt_navigator   --ros-args --params-file "$CFG"
run collision_monitor /opt/ros/humble/lib/nav2_collision_monitor/collision_monitor --ros-args --params-file "$CFG"
sleep 4
run lifecycle_nav /opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager --ros-args -r __node:=lifecycle_manager_navigation --params-file "$CFG"
echo "  -> activando Nav2 (lifecycle ~12 s)"
sleep 12
# 7) motor real (autonomo + stall-breaker + deadman) + soporte web
run car_control python3 ~/robocar/src/robocar_pkg/robocar_pkg/car_control_node.py --ros-args -p autonomous_start:=true
run goal_relay  python3 ~/robocar/src/robocar_pkg/robocar_pkg/goal_relay_node.py
run nav_config  python3 ~/robocar/src/robocar_pkg/robocar_pkg/nav_config_node.py
run map_areas   python3 ~/robocar/src/robocar_pkg/robocar_pkg/map_areas_node.py
run map_edit    python3 ~/robocar/src/robocar_pkg/robocar_pkg/map_edit_node.py
run health      python3 ~/robocar/src/robocar_pkg/robocar_pkg/robocar_health_node.py
run rosbridge   ros2 launch rosbridge_server rosbridge_websocket_launch.xml
sleep 2

echo ""
echo "======================================================================"
echo " NAVEGACION REAL (Cartographer-localization) lista. Mapa: $(basename "$PB")"
echo "   - Localizacion robusta (no deriva); el laser encaja con el mapa."
echo "   - RUEDAS AL AIRE el primer arranque; velocidad limitada a 0.25 m/s."
echo "   - Parada de emergencia:  bash ~/robocar/scripts/estop.sh"
echo "======================================================================"
