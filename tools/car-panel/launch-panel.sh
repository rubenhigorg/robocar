#!/bin/bash
# Arranca el panel web del Robocar (en la Pi):
#   modelo+TF, sensores, rosbridge (ws :9090) y la web estatica (http :8080).
# Uso:  bash ~/robocar/tools/car-panel/launch-panel.sh
# Ver:  http://robocar.local:8080
# NOTA: NO arranca car_control_node (motores inertes). El LIDAR es opcional.

source /opt/ros/humble/setup.bash
source /home/lab/robocar/src/install/setup.sh
source /home/lab/robocar/.venv/bin/activate 2>/dev/null

cd /home/lab/robocar

nohup ros2 launch robocar_description description.launch.py > ~/panel_rsp.log 2>&1 &
nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml > ~/panel_bridge.log 2>&1 &
nohup ros2 run robocar_pkg accelerometer_node > ~/panel_imu.log 2>&1 &
nohup ros2 run robocar_pkg distance_node > ~/panel_us.log 2>&1 &
nohup ros2 run robocar_pkg energy_node > ~/panel_energy.log 2>&1 &

# LIDAR si esta conectado (saltar con NOLIDAR=1 — su motor puede hundir el 5V)
if [ -e /dev/ttyUSB0 ] && [ -z "$NOLIDAR" ]; then
  sudo chmod 666 /dev/ttyUSB0 2>/dev/null
  nohup ros2 run rplidar_ros rplidar_node --ros-args \
    -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=460800 -p frame_id:=laser \
    > ~/panel_lidar.log 2>&1 &
  echo "LIDAR detectado y lanzado"
fi

# web estatica
nohup python3 -m http.server 8080 --directory /home/lab/robocar/tools/car-panel/static \
  > ~/panel_web.log 2>&1 &

sleep 4
echo "── Panel del Robocar ──"
echo "web:       http://robocar.local:8080"
echo "rosbridge: ws://robocar.local:9090"
ros2 topic list 2>/dev/null | grep -vE "^/(parameter|rosout|client|connected)" | sed "s/^/topic:      /"
