#!/bin/bash
# Reinicia SOLO los servidores de Nav2 (no el banco) leyendo el yaml actual.
# Lo usa nav_config para aplicar parametros que Smac no admite en caliente
# (motion_model / minimum_turning_radius). El banco (sim_motion/sensors/map) sigue vivo.
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1
CFG=~/robocar/src/robocar_pkg/config/nav2_bench.yaml
for pass in 1 2; do for n in collision_monitor bt_navigator controller_server planner_server behavior_server lifecycle_manager; do pkill -9 -f "$n" 2>/dev/null; done; sleep 1; done
sleep 1
nohup /opt/ros/humble/lib/nav2_planner/planner_server --ros-args --params-file $CFG >/tmp/planner.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_controller/controller_server --ros-args -r /cmd_vel:=/cmd_vel_raw --params-file $CFG >/tmp/controller.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_behaviors/behavior_server --ros-args --params-file $CFG >/tmp/behavior.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_bt_navigator/bt_navigator --ros-args --params-file $CFG >/tmp/btnav.log 2>&1 & disown
nohup /opt/ros/humble/lib/nav2_collision_monitor/collision_monitor --ros-args --params-file $CFG >/tmp/colmon.log 2>&1 & disown
sleep 4
nohup /opt/ros/humble/lib/nav2_lifecycle_manager/lifecycle_manager --ros-args -r __node:=lifecycle_manager_navigation --params-file $CFG >/tmp/lifecycle.log 2>&1 & disown
echo "nav2 reiniciado"
