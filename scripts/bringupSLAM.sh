#!/bin/bash
# bringupSLAM.sh - MODO "GENERAR MAPA REAL": cartografia del piso con Cartographer + teleop web.
#
# Cadena real (validada en A1): description(TF) + RPLIDAR(/scan) + encoder + IMU + EKF(odometria)
# + Cartographer(/map + map->odom) + car_control(motor por /cmd_vel) + rosbridge + panel web.
#
# Uso:  bash ~/robocar/scripts/bringupSLAM.sh
# Luego: abrir  http://<IP-del-robot>:8080/cartografia.html  y conducir para ir dibujando el mapa.
# Guardar:  bash ~/robocar/scripts/save_map.sh piso_real
source /opt/ros/humble/setup.bash
source ~/robocar/src/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID=0 ROS_LOCALHOST_ONLY=1

# 0) Matar cualquier sim/Nav2/SLAM previo (chocan por /scan, odometria, TF y /cmd_vel).
for n in sim_motion_node sim_sensors_node sim_map_grid_node trajectory_nav_node \
         planner_server controller_server behavior_server bt_navigator collision_monitor \
         nav2_amcl goal_relay_node nav_config_node map_areas_node particle_relay_node \
         nav2_lifecycle_manager cartographer_node occupancy_grid_node rplidar_node \
         encoder_node accelerometer_node car_control_node ekf_node rf2o_laser_odometry \
         wheel_twistcov_node odom_cov_node steer_yaw_node robot_state_publisher \
         rosbridge_websocket "http.server 8080"; do
  pkill -9 -f "$n" 2>/dev/null
done
sleep 2

L=~/robocar/logs; mkdir -p "$L"
run(){ local name="$1"; shift; echo "  -> $name"; nohup "$@" >"$L/$name.log" 2>&1 & disown; }

# 1) TF del modelo (robot_state_publisher: base_link -> laser/imu/ruedas)
run description ros2 launch robocar_description description.launch.py
sleep 2
# 2) LIDAR real -> /scan (frame 'laser', C1 @460800 por UART)
run rplidar    ros2 run rplidar_ros rplidar_node --ros-args \
                 -p serial_port:=/dev/serial0 -p serial_baudrate:=460800 \
                 -p frame_id:=laser -p scan_mode:=Standard -p angle_compensate:=true
# 3) Sensores I2C
run encoder    ros2 run robocar_pkg encoder_node
run imu        ros2 run robocar_pkg accelerometer_node
sleep 2
# 4) Odometria fusionada (EKF) -> /odometry/filtered + TF odom->base_link
run ekf        ros2 launch robocar_pkg ekf.launch.py
sleep 3
# 5) Cartographer -> /map (OccupancyGrid) + TF map->odom
run slam       ros2 launch robocar_slam slam.launch.py
# 6) Control del motor/direccion (teleop por /cmd_vel; deadman 0.5 s -> neutro)
run car_control ros2 run robocar_pkg car_control_node
# 7) Web: rosbridge (:9090) + panel (:8080)
run rosbridge  ros2 launch rosbridge_server rosbridge_websocket_launch.xml
run panel      bash -c "cd ~/robocar/tools/car-panel/static && exec python3 -m http.server 8080"
sleep 2

echo ""
echo "======================================================================"
echo " MODO MAPA REAL listo. Abre en el movil/PC (misma red):"
echo "   http://$(hostname -I | awk '{print $1}'):8080/cartografia.html"
echo " Conduce despacio, con bucles cerrados, para ir cerrando el mapa."
echo " Guardar el mapa:  bash ~/robocar/scripts/save_map.sh piso_real"
echo "======================================================================"
