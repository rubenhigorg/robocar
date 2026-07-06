#!/bin/bash
# Arranca el panel web del Robocar (en la Pi):
#   modelo+TF, sensores, rosbridge (ws :9090) y la web estatica (http :8080).
# Uso:  bash ~/robocar/tools/car-panel/launch-panel.sh
# Ver:  http://robocar.local:8080
# NOTA: NO arranca car_control_node (motores inertes). El LIDAR es opcional.

source /opt/ros/humble/setup.bash
source /home/lab/robocar/src/install/setup.sh

cd /home/lab/robocar

# Con python del sistema (el venv NO tiene netifaces/tornado y mata rosbridge):
nohup ros2 launch robocar_description description.launch.py > ~/panel_rsp.log 2>&1 &
nohup ros2 launch rosbridge_server rosbridge_websocket_launch.xml > ~/panel_bridge.log 2>&1 &
nohup python3 -m http.server 8080 --directory /home/lab/robocar/tools/car-panel/static \
  > ~/panel_web.log 2>&1 &

# El venv SOLO para los nodos de sensores (drivers adafruit/smbus/GPIO):
source /home/lab/robocar/.venv/bin/activate 2>/dev/null
nohup ros2 run robocar_pkg accelerometer_node > ~/panel_imu.log 2>&1 &
nohup ros2 run robocar_pkg distance_node > ~/panel_us.log 2>&1 &
nohup ros2 run robocar_pkg energy_node > ~/panel_energy.log 2>&1 &
nohup ros2 run robocar_pkg encoder_node > ~/panel_encoder.log 2>&1 &

# LIDAR: puerto por LIDAR_PORT, o autodeteccion — USB primero, y si no, la
# UART de los pines (/dev/ttyS0, conexion definitiva desde jul 2026; validada
# a 460800 con la consola serie deshabilitada). Saltar con NOLIDAR=1.
# Permisos: el usuario lab pertenece al grupo dialout.
LIDAR_DEV="${LIDAR_PORT:-}"
if [ -z "$LIDAR_DEV" ]; then
  if [ -e /dev/ttyUSB0 ]; then LIDAR_DEV=/dev/ttyUSB0
  elif [ -e /dev/ttyS0 ]; then LIDAR_DEV=/dev/ttyS0; fi
fi
if [ -n "$LIDAR_DEV" ] && [ -z "$NOLIDAR" ]; then
  nohup ros2 run rplidar_ros rplidar_node --ros-args \
    -p serial_port:="$LIDAR_DEV" -p serial_baudrate:=460800 -p frame_id:=laser \
    > ~/panel_lidar.log 2>&1 &
  echo "LIDAR lanzado en $LIDAR_DEV"
fi

sleep 6
echo "── Panel del Robocar ──"
echo "web:       http://robocar.local:8080"
echo "rosbridge: ws://robocar.local:9090"
ros2 topic list 2>/dev/null | grep -vE "^/(parameter|rosout|client|connected)" | sed "s/^/topic:      /"
