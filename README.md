<div align="center">

# 🚗 Robocar

**Robot coche autónomo de bajo coste con ROS2, visión artificial y LIDAR**

[![ROS2 Iron](https://img.shields.io/badge/ROS2-Iron-blue?logo=ros)](https://docs.ros.org/en/iron/)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](src/robocar_pkg/LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue?logo=github)](https://rubenhigorg.github.io/robocar)

Construido con componentes comerciales (~293 €) · Raspberry Pi 4 · OpenCV · ROS2 Iron

[**📖 Documentación completa**](https://rubenhigorg.github.io/robocar)

</div>

---

## Qué es Robocar

Robocar es un vehículo autónomo a escala construido con componentes comerciales de bajo coste. El proyecto nació como Trabajo de Fin de Grado en la Universidad Politécnica de Madrid y ha evolucionado a lo largo de tres trabajos académicos:

| Trabajo | Descripción |
|---|---|
| **TFG 1** — Diseño y Construcción | Hardware, sensores, electrónica, nodos ROS2 y panel Node-RED |
| **TFG 2** — Seguimiento de Carril | Lane-following con OpenCV, Transformada de Hough, Kalman y PID |
| **TFM** — Navegación con LIDAR y LLMs | SLAM con RPLidar C1, navegación Nav2 e interfaz natural con LLMs vía MCP |

## Características principales

- 🎮 **Conducción manual** con mando PS3 y **modo autónomo** con lane-following
- 👁️ **Visión artificial** — detección de carril con OpenCV, Kalman y control PID
- 📡 **LIDAR** — mapeo del entorno con RPLidar C1 y SLAM (Cartographer)
- 🧭 **Navegación autónoma** — planificación de rutas con Nav2
- 🤖 **Interfaz natural** — control por lenguaje natural mediante LLMs y MCP
- 📊 **Dashboard** — monitorización en tiempo real con Node-RED
- 🔋 **Monitorización energética** — voltaje y corriente de baterías (INA3221/INA226)
- 🛑 **Seguridad** — parada de emergencia por ultrasonidos (3× HC-SR04)

## Arquitectura

El sistema se compone de nodos ROS2 independientes que se comunican por topics:

```
                    ┌─────────────┐
  Mando PS3 ──────►│ car_control │──────► Motores + Dirección
                    │    _node    │            (PCA9685)
  /lane_info ─────►│             │
                    └─────────────┘
                          ▲
  ┌──────────┐    ┌───────┴───────┐
  │  camera  │───►│  processing   │
  │  _node   │    │    _node      │
  └──────────┘    └───────────────┘

  ┌──────────┐  ┌──────────┐  ┌──────────────┐
  │ distance │  │  energy  │  │ accelerometer│
  │  _node   │  │  _node   │  │    _node     │
  └──────────┘  └──────────┘  └──────────────┘
```

| Nodo | Topic | Descripción |
|---|---|---|
| `camera_node` | `/camera_image` | Captura 640×480 @ ~3 FPS |
| `processing_node` | `/lane_info` | Detección de carril (OpenCV + Kalman + PID) |
| `car_control_node` | `/joy`, `/lane_info` | Control de motores y dirección |
| `distance_node` | `/ultrasound_data` | 3× HC-SR04 ultrasonidos @ 10 Hz |
| `energy_node` | `/energy` | Voltajes (INA3221) + corriente (INA226) |
| `accelerometer_node` | `/imu` | IMU 6 ejes (MPU6050) |

## Hardware

| Componente | Modelo | Función |
|---|---|---|
| Computador | Raspberry Pi 4 (4 GB) | Procesamiento central |
| Cámara | USB 640×480 | Visión artificial |
| LIDAR | RPLidar C1 | Mapeo 360° del entorno |
| Ultrasonidos | 3× HC-SR04 | Detección de obstáculos |
| IMU | MPU6050 | Acelerómetro + giroscopio |
| Controlador servos | PCA9685 (16 ch) | Motores y dirección |
| Monitor energético | INA3221 + INA226 | Voltaje y corriente baterías |
| Mando | PS3 DualShock | Control manual |

> **Coste total:** ~293 € con componentes comerciales

## Quick Start

```bash
# 1. Entorno ROS2
source /opt/ros/iron/setup.bash

# 2. Dependencias Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Compilar paquetes ROS2
cd src && colcon build && source install/setup.sh && cd ..

# 4. Lanzar todos los nodos
bash launch.sh

# 5. Dashboard Node-RED (opcional)
bash nodered.sh
```

### Mando PS3

```bash
ros2 launch teleop_twist_joy teleop-launch.py
```

Cambio manual ↔ autónomo: **botón X** del mando.

## Estructura del repositorio

```
robocar/
├── src/
│   ├── robocar_pkg/          # Nodos ROS2 (Python)
│   │   ├── robocar_pkg/      # camera, processing, car_control, distance, energy, accelerometer
│   │   ├── lib/              # Drivers hardware (INA3221, INA226, MPU6050, OpenCV)
│   │   └── test/             # Tests
│   ├── messages_pkg/         # Mensajes custom (Distance.msg, Energy.msg)
│   └── teleop_twist_joy/     # Paquete joystick
├── docs/                     # Documentación MkDocs
├── hardware/                 # Esquemático KiCad
├── flows.json                # Flujos Node-RED
├── launch.sh                 # Script lanzamiento producción
└── mkdocs.yml                # Configuración documentación web
```

## Tests y linting

```bash
# Tests
colcon test --packages-select robocar_pkg
colcon test-result --verbose

# Linting
ament_flake8 src/robocar_pkg
ament_pep257 src/robocar_pkg
```

## Documentación

La documentación completa está disponible en **[rubenhigorg.github.io/robocar](https://rubenhigorg.github.io/robocar)**, incluyendo:

- Diseño y construcción del hardware
- Pipeline de visión artificial y control
- SLAM con Cartographer y RPLidar C1
- Navegación autónoma con Nav2
- Interfaz natural con LLMs y MCP

## Autores

| | Nombre | Contribución |
|---|---|---|
| 👤 | **Rubén Higuera Castillo** | TFG 1, TFG 2, TFM |
| 👤 | **Kento Reinoso** | TFG 1 |

## Licencia

Distribuido bajo la licencia Apache 2.0. Ver [`LICENSE`](src/robocar_pkg/LICENSE) para más información.
