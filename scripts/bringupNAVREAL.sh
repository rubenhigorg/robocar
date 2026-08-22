#!/bin/bash
# bringupNAVREAL.sh - NAVEGACION REAL (Fase C): hardware real + map_server (mapa cartografiado
# guardado) + AMCL + Nav2. Sustituye la cadena sim del banco por la real, dejando Nav2 + web igual.
#
#   Cadena:  description(TF) + RPLIDAR(/scan) + encoder + IMU + EKF(/odometry/filtered)
#            + map_server(/map) + AMCL(map->odom) + Nav2(planner/controller/behavior/bt/collision)
#            + car_control(/cmd_vel) + goal_relay/nav_config/map_areas + rosbridge/health
#   controller -> /cmd_vel_raw -> collision_monitor(LIDAR) -> /cmd_vel -> car_control (deadman 0.5s)
#
# Uso:  bash bringupNAVREAL.sh [nombre_mapa]     (por defecto el .yaml mas reciente de ~/robocar/maps)
# SEGURIDAD: primer arranque con RUEDAS AL AIRE. Parada: bash ~/robocar/scripts/estop.sh
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1
CFG=~/robocar/src/robocar_pkg/config/nav2_real.yaml
MAPS=~/robocar/maps
MAP="${1:-}"
[ -z "$MAP" ] && MAP="$(ls -t $MAPS/*.yaml 2>/dev/null | head -1 | xargs -r basename | sed 's/\.yaml$//')"
MAPYAML="$MAPS/$MAP.yaml"
if [ ! -f "$MAPYAML" ]; then echo "ERROR: no existe el mapa $MAPYAML (elige uno de: $(ls $MAPS/*.yaml 2>/dev/null | xargs -r -n1 basename))"; exit 1; fi
echo "  Mapa de localizacion (AMCL): $MAP  ($MAPYAML)"

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
# 3) sensores I2C
run encoder ros2 run robocar_pkg encoder_node
run imu     ros2 run robocar_pkg accelerometer_node
sleep 2
# 4) EKF -> /odometry/filtered + TF odom->base_link
run ekf ros2 launch robocar_pkg ekf.launch.py; sleep 3
# 5) MAPA cartografiado -> /map (map_server, activado por lifecycle_manager_localization)
run map_server /opt/ros/humble/lib/nav2_map_server/map_server --ros-args --params-file "$CFG" -p yaml_filename:="$MAPYAML"
# 6) Nav2 + AMCL (controller saca /cmd_vel_raw; collision_monitor -> /cmd_vel)
run planner    /opt/ros/humble/lib/nav2_planner/planner_server        --ros-args --params-file "$CFG"
run controller /opt/ros/humble/lib/nav2_controller/controller_server  --ros-args -r /cmd_vel:=/cmd_vel_raw --params-file "$CFG"
run behavior   /opt/ros/humble/lib/nav2_behaviors/behavior_server     --ros-args --params-file "$CFG"
run bt_navigator /opt/ros/humble/lib/nav2_bt_navigator/bt_navigator   --ros-args --params-file "$CFG"
run collision_monitor /opt/ros/humble/lib/nav2_collision_monitor/collision_monitor --ros-args --params-file "$CFG"
run amcl       /opt/ros/humble/lib/nav2_amcl/amcl                      --ros-args --params-file "$CFG"
sleep 4
run lifecycle_nav /opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager --ros-args -r __node:=lifecycle_manager_navigation   --params-file "$CFG"
run lifecycle_loc /opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager --ros-args -r __node:=lifecycle_manager_localization --params-file "$CFG"
echo "  -> activando Nav2 (lifecycle ~12 s)"
sleep 12
# 7) motor real (deadman 0.5s -> neutro) + soporte web
run car_control  ros2 run robocar_pkg car_control_node
run goal_relay   python3 ~/robocar/src/robocar_pkg/robocar_pkg/goal_relay_node.py
run nav_config   python3 ~/robocar/src/robocar_pkg/robocar_pkg/nav_config_node.py
run map_areas    python3 ~/robocar/src/robocar_pkg/robocar_pkg/map_areas_node.py
run particle_relay python3 ~/robocar/src/robocar_pkg/robocar_pkg/particle_relay_node.py
run map_edit     python3 ~/robocar/src/robocar_pkg/robocar_pkg/map_edit_node.py
run health       python3 ~/robocar/src/robocar_pkg/robocar_pkg/robocar_health_node.py
run rosbridge    ros2 launch rosbridge_server rosbridge_websocket_launch.xml
sleep 2

echo ""
echo "======================================================================"
echo " NAVEGACION REAL lista. Mapa: $MAP"
echo "   1) Abre la web y fija la pose real del coche (2D Pose Estimate)."
echo "   2) RUEDAS AL AIRE en el primer arranque; velocidad limitada a 0.25 m/s."
echo "   3) Parada de emergencia:  bash ~/robocar/scripts/estop.sh"
echo "======================================================================"
