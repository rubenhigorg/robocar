# 🚗 Robocar

Robot coche autónomo construido con componentes comerciales de bajo coste (~293€), capaz de seguimiento de carril mediante visión artificial. Funciona con ROS2 (Iron) sobre Raspberry Pi 4.

## 📖 Documentación

Este proyecto es el resultado de dos Trabajos de Fin de Grado y un Trabajo de Fin de Máster (en desarrollo):

| Trabajo | Descripción |
|---|---|
| [**TFG 1: Diseño y Construcción**](docs/tfg1-construccion/README.md) | Hardware, sensores, electrónica, software ROS2 y panel Node-RED |
| [**TFG 2: Seguimiento de Carril**](docs/tfg2-lane-following/README.md) | Lane-following con OpenCV, Kalman y PID |
| [**TFM** (en curso)](docs/tfm/README.md) | Extensión con LIDAR |

👉 [**Ver toda la documentación**](docs/README.md)

## Arquitectura

### Nodos ROS2

| Nodo | Topic | Función |
|---|---|---|
| `camera_node` | `/camera_image` | Captura frames 640×480 a ~3 FPS |
| `processing_node` | `/lane_info` | Detecta carriles (OpenCV + Kalman + PID) |
| `car_control_node` | Suscribe `/joy`, `/lane_info` | Controla motores y dirección (manual/autónomo) |
| `distance_node` | `/ultrasound_data` | 3× HC-SR04 + KY-032 a 10 Hz |
| `energy_node` | `/energy` | Voltajes (INA3221) y corriente (INA226) |
| `accelerometer_node` | `/imu` | Acelerómetro + giroscopio (MPU6050) |

### Modos de conducción

- **Manual:** Joystick PS3 controla dirección y aceleración
- **Autónomo:** Seguimiento de carril por visión artificial
- **Cambio de modo:** Botón X del mando PS3

## Quick Start

```bash
# Configurar entorno ROS2
source /opt/ros/iron/setup.bash

# Instalar dependencias Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Construir paquetes ROS2
cd src
colcon build
source install/setup.sh

# Lanzar todos los nodos
bash launch.sh

# Lanzar Node-RED (panel de control)
bash nodered.sh
```

### Nodo del joystick

```bash
ros2 launch teleop_twist_joy teleop-launch.py
```

> Por defecto usa mando PS3. Ver readme del paquete `teleop_twist_joy` para otros mandos.

### Node-RED (instalación desde cero)

```bash
npm install -g --unsafe-perm node-red rclnodejs cron
cd /home/lab/edu_nodered_ros2_plugin
npm install -g .
```

Para mensajes custom (ejecutar como root desde `/usr/lib/node_modules/rclnodejs/scripts`):

```bash
source /opt/ros/iron/setup.sh
source /home/ros2/robocar/src/install/setup.sh
npm run generate-messages
```

## Tests

```bash
colcon test --packages-select robocar_pkg
colcon test-result --verbose
```

## Lint

```bash
ament_flake8 src/robocar_pkg
ament_pep257 src/robocar_pkg
```
