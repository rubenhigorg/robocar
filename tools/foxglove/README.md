# Panel de control del Robocar (layout Foxglove/Lichtblick)

Layout versionado del panel de control: **3D del coche** (URDF + TF + `/scan` del LIDAR)
+ **IMU** (aceleración y giro) + **ultrasonidos** + **energía**.

## Requisitos (en la Pi)

```bash
# lo lanza todo la sesión de visualización:
ros2 launch robocar_description description.launch.py &   # modelo + TF
ros2 run foxglove_bridge foxglove_bridge &                 # websocket :8765
ros2 run robocar_pkg accelerometer_node &                  # /imu
ros2 run robocar_pkg distance_node &                       # /ultrasound_data
ros2 run robocar_pkg energy_node &                         # /energy
# opcional, si el LIDAR está conectado:
ros2 run rplidar_ros rplidar_node --ros-args -p serial_port:=/dev/ttyUSB0 \
  -p serial_baudrate:=460800 -p frame_id:=laser &          # /scan
```

## Uso (en el Mac / cualquier equipo)

1. Abrir **Foxglove Studio** o **Lichtblick**.
2. *Open connection…* → **Foxglove WebSocket** → `ws://robocar.local:8765`.
3. Menú de **Layouts** (barra lateral) → **Import from file…** → este
   `robocar-layout.json`.

Si se ajusta el panel a mano y se quiere conservar: *Export layout…* y commitear
el JSON actualizado aquí.
