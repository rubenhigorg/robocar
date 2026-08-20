#!/bin/bash
# ============================================================================
# POLITICA DE ARRANQUE DEL BANCO (O6)
#   - Nodos propios (robocar_pkg): se lanzan por PYTHON3 DIRECTO desde src/ (no
#     'ros2 run'). Asi se editan SIN recompilar (colcon en la Pi4 es lento/OOM)
#     y src/ es la unica fuente de verdad.
#   - Nodos stock de Nav2: BINARIO DIRECTO /opt/ros/humble/lib/... (no 'ros2 run'),
#     para no dejar wrappers de ~23 MB (O4).
#   - Todo el stack corre con ROS_LOCALHOST_ONLY=1 (DDS por 'lo', fix dual-interface).
#   OJO: reiniciar en caliente un nodo que publica TF (sim_motion=odom->base_link,
#   sim_map_grid=map->odom) corrompe la cache TF/costmap -> relanzar con ESTE script.
# ============================================================================
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1
CFG=~/robocar/src/robocar_pkg/config/nav2_bench.yaml
# rosbridge + panel
pgrep -f rosbridge_websocket >/dev/null || ( nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml >/tmp/rosbridge.log 2>&1 & )
pgrep -f "http.server 8080" >/dev/null || ( cd ~/robocar/tools/car-panel/static; nohup python3 -m http.server 8080 >/tmp/panel.log 2>&1 & )
# limpiar todo lo que pueda chocar
for pass in 1 2 3; do for n in collision_monitor bt_navigator controller_server planner_server behavior_server lifecycle_manager waypoint_follower velocity_smoother smoother_server nav_config map_areas goal_relay trajectory_nav sim_map_grid sim_sensors sim_motion ekf_node ekf_filter ekf.launch car_control_node encoder_node accelerometer_node steer_yaw_node robot_state_publisher; do pkill -9 -f "$n" 2>/dev/null; done; sleep 1; done
sleep 2
# --- banco (planta simulada) ---
nohup ros2 launch robocar_description description.launch.py >/tmp/desc.log 2>&1 & disown
sleep 2
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/sim_motion_node.py --ros-args -p cmd_mode:=twist -p rate_hz:=20.0 >/tmp/sm.log 2>&1 & disown
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/sim_sensors_node.py >/tmp/ss.log 2>&1 & disown   # src parcheado (obstaculos)
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/sim_map_grid_node.py >/tmp/smg.log 2>&1 & disown
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/trajectory_nav_node.py --ros-args -r /cmd_vel:=/cmd_vel_raw >/tmp/tn.log 2>&1 & disown   # RUTA: tambien pasa por el collision_monitor
sleep 4
# (sin mapa de arranque: la web empieza limpia; el usuario carga su mapa cuando quiere)
# --- Nav2 ---
nohup /opt/ros/humble/lib/nav2_planner/planner_server --ros-args --params-file $CFG >/tmp/planner.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_controller/controller_server --ros-args -r /cmd_vel:=/cmd_vel_raw --params-file $CFG >/tmp/controller.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_behaviors/behavior_server --ros-args --params-file $CFG >/tmp/behavior.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_bt_navigator/bt_navigator --ros-args --params-file $CFG >/tmp/btnav.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_collision_monitor/collision_monitor --ros-args --params-file $CFG >/tmp/colmon.log 2>&1 & disown   # reflejo IR
sleep 4
nohup /opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager --ros-args -r __node:=lifecycle_manager_navigation --params-file $CFG >/tmp/lifecycle.log 2>&1 & disown
sleep 12
# relay del destino: /goal_pose (web) -> accion NavigateToPose (Nav2)
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/goal_relay_node.py >/tmp/gr.log 2>&1 & disown
# config de navegacion (contrato /nav_config para web y LLM)
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/nav_config_node.py >/tmp/nc.log 2>&1 & disown
nohup python3 ~/robocar/src/robocar_pkg/robocar_pkg/map_areas_node.py >/tmp/ma.log 2>&1 & disown   # zonas del mapa (cocina, bano...)
sleep 2
echo "=== nodos Nav2 ==="; ros2 node list 2>/dev/null | grep -iE 'planner|controller|behavior|bt_nav|lifecycle|goal_relay|trajectory' | sort
echo "=== estado lifecycle ==="
for s in planner_server controller_server behavior_server bt_navigator; do echo -n "$s: "; timeout 5 ros2 lifecycle get /$s 2>/dev/null || echo "no responde"; done
