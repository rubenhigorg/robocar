#!/bin/bash
# stopall.sh - APAGA TODO el robocar: los nodos de cualquier entorno (banco / cartografia / nav real)
# + la capa por-stack (rosbridge, TF, health). NO toca el LANZADOR (robocar_launcher, que sirve el
# panel :8080 y arranca/para entornos). Primitiva de limpieza: cada bringup empieza por aqui.
for n in \
  sim_motion_node sim_sensors_node sim_map_grid_node sim_map_loader_node trajectory_nav_node \
  nav2_planner/planner_server nav2_controller/controller_server nav2_behaviors nav2_bt_navigator \
  nav2_collision_monitor nav2_amcl nav2_lifecycle_manager nav2_map_server \
  waypoint_follower velocity_smoother smoother_server \
  goal_relay_node nav_config_node map_areas_node particle_relay_node \
  cartographer_node cartographer_occupancy_grid_node "robocar_slam slam.launch" \
  slam_checkpoint_node map_edit_node robocar_health_node \
  rplidar_node encoder_node accelerometer_node car_control_node steer_yaw_node \
  ekf_node ekf.launch rf2o_laser_odometry wheel_twistcov_node odom_cov_node \
  robot_state_publisher description.launch \
  rosbridge_websocket "ros2 launch rosbridge_server" ; do
  pkill -9 -f "$n" 2>/dev/null
done
sleep 1
echo "stopall: todo parado (el lanzador sigue vivo)"
