# robocar_description

Modelo URDF/xacro del Robocar y su árbol TF (**hito 0.3** del TFM).

## Estado

**Borrador funcional con medidas placeholder** (valores típicos de RC 1/10). Todas las
medidas a rellenar están concentradas al inicio de `urdf/robocar.urdf.xacro`, marcadas
con `TODO(medir)`.

## Checklist de medidas (con el coche y un metro)

| Medida | Propiedad xacro | Cómo medirla |
|---|---|---|
| Batalla | `wheelbase` | Centro eje trasero → centro eje delantero |
| Vía | `track_width` | Centro rueda izq → centro rueda der |
| Radio de rueda | `wheel_radius` | Diámetro / 2 |
| Ancho de rueda | `wheel_width` | — |
| Chasis (L×W×H) | `chassis_*` | Caja aproximada que envuelve el coche |
| Voladizo trasero | `chassis_rear_overhang` | Del eje trasero al final del chasis |
| LIDAR | `laser_x`, `laser_z` | Desde el centro del eje trasero al centro del RPLidar; z = altura del plano de barrido sobre el eje |
| IMU | `imu_x`, `imu_z` | Posición del MPU6050 |
| Cámara | `camera_x`, `camera_z` | — |
| Ultrasonidos | `us_x`, `us_y`, `us_z` | x/z del central; y = separación lateral de los laterales |

Origen de referencia: **centro del eje trasero** (convención Ackermann). x adelante,
y izquierda, z arriba.

## Uso (en la Pi, Humble)

```bash
sudo apt install ros-humble-xacro   # una vez
cd ~/robocar/src && colcon build --packages-select robocar_description
source install/setup.sh
ros2 launch robocar_description description.launch.py
```

Verificación rápida del TF: `ros2 run tf2_tools view_frames` o abrir el panel 3D de
**Foxglove** (con `foxglove_bridge` corriendo) y añadir el modelo.

## Frames publicados

`base_footprint → base_link → {4 ruedas, laser, imu_link, camera_link, ultrasound_{left,center,right}}`

- `laser`: el frame que usa `rplidar_ros` en `/scan` — Cartographer lo consumirá tal cual.
- `imu_link`: usarlo como `frame_id` en `accelerometer_node` (hito 0.5).
