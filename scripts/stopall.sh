#!/bin/bash
# ============================================================================
# stopall.sh (v2) - TEARDOWN AUTORITARIO Y FIABLE del robocar.
#
#   Problema historico: matar por NOMBRE deja "demonios" (hijos, wrappers, cosas
#   lanzadas de otra forma) y FastDDS deja SEGMENTOS en /dev/shm que los pkill -9
#   no limpian -> un participante nuevo (rosbridge) se cuelga sobre esa basura y
#   no llega a atar :9090 ("sin conexion", "no hay mapas").
#
#   Solucion:
#     1) matar por GRUPO DE PROCESO (kill -9 -PGID) -> cae el arbol ENTERO, no se
#        escapa ningun hijo, sin depender de acertar el nombre.
#     2) red de seguridad por nombre (por si algo quedo suelto).
#     3) limpiar la memoria compartida de FastDDS (/dev/shm/fastrtps_*) y parar el
#        daemon de ros2 (cachea grafo obsoleto).
#     4) VERIFICAR y reportar (procesos ROS restantes + segmentos SHM).
#   NUNCA toca el LANZADOR (robocar_launcher.py, que sirve el panel :8080).
# ============================================================================
set +e
LAUNCHER="robocar_launcher.py"
SELF_PGID=$(ps -o pgid= -p $$ | tr -d ' ')

# procesos ROS/robocar por los que localizar sus GRUPOS de proceso
ROSPAT='/opt/ros/|robocar/src|robocar_pkg|rosbridge_server|rosapi|rplidar|nav2_|cartographer|rf2o|/ekf|amcl|robot_state_publisher|robocar_slam|robocar_description|map_server|lifecycle_manager|collision_monitor|sim_motion|sim_sensors|sim_map|goal_relay|nav_config|map_areas|particle_relay|slam_checkpoint|map_edit|sim_map_loader|robocar_health|trajectory_nav|encoder_node|accelerometer_node|car_control|steer_yaw|odom_cov|wheel_twist'

collect_pgids(){
  ps -eo pgid,args | grep -E "$ROSPAT" | grep -vE "grep|$LAUNCHER" \
    | awk '{print $1}' | sort -u | grep -vx "$SELF_PGID"
}

# 1) matar los GRUPOS: primero TERM (salida limpia), luego KILL
for pg in $(collect_pgids); do kill -TERM -"$pg" 2>/dev/null; done
sleep 2
for pg in $(collect_pgids); do kill -9 -"$pg" 2>/dev/null; done
sleep 1

# 2) red de seguridad por nombre (por si algo quedo en el grupo del lanzador o suelto)
for n in rosbridge_websocket rosapi_node rplidar_node cartographer_node cartographer_occupancy_grid_node \
         nav2_planner nav2_controller nav2_behaviors nav2_bt_navigator nav2_collision_monitor nav2_amcl \
         nav2_map_server nav2_lifecycle_manager nav2_waypoint_follower nav2_velocity_smoother \
         ekf_node ekf_filter rf2o_laser_odometry encoder_node accelerometer_node car_control_node \
         steer_yaw_node odom_cov_node wheel_twistcov_node robot_state_publisher \
         sim_motion_node sim_sensors_node sim_map_grid_node sim_map_loader_node trajectory_nav_node \
         goal_relay_node nav_config_node map_areas_node particle_relay_node slam_checkpoint_node \
         map_edit_node robocar_health_node "ros2 launch rosbridge" "ros2 launch robocar"; do
  pkill -9 -f "$n" 2>/dev/null
done
sleep 1

# 3) higiene DDS: SHM obsoleta (raiz del cuelgue de rosbridge) + daemon ros2
rm -f /dev/shm/fastrtps_* /dev/shm/sem.fastrtps_* 2>/dev/null
( source /opt/ros/humble/setup.bash 2>/dev/null; ros2 daemon stop >/dev/null 2>&1 ) &
sleep 1

# 4) verificacion
LEFT=$(ps -eo args | grep -E "$ROSPAT" | grep -vE "grep|$LAUNCHER" | wc -l | tr -d ' ')
SHM=$(ls /dev/shm/ 2>/dev/null | grep -ic fastrtps)
echo "stopall v2 -> procesos ROS restantes=$LEFT · segmentos fastrtps=$SHM · lanzador intacto"
[ "$LEFT" = "0" ] && [ "$SHM" = "0" ] && echo "stopall v2 -> LIMPIO" || echo "stopall v2 -> AVISO: quedan restos (revisar)"
