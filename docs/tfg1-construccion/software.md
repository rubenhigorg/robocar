# Software: ROS2 y Node-RED

[← Volver al TFG1](README.md)

## ROS2 (Robot Operating System 2)

### Conceptos Básicos

ROS2 es un framework open-source que proporciona herramientas y librerías para aplicaciones robóticas. Características clave para este proyecto:

- **Arquitectura distribuida y modular** — los nodos se comunican eficientemente
- **DDS (Data Distribution Service)** — comunicación fiable y segura
- **No tiempo real** — no es un requisito de este proyecto

Conceptos aplicados:
- **Nodes:** Unidad funcional (un nodo por responsabilidad)
- **Topics:** Bus de comunicación entre nodos, modelo publicador/suscriptor
- **Messages:** Estructuras de datos para intercambio de información (tipos primitivos y personalizados)

### Diagrama de Nodos

| Nodo | Publica | Tipo Mensaje | Se suscribe a |
|---|---|---|---|
| **camera_node** | `/camera_image` | `sensor_msgs/Image` | — |
| **energy_node** | `/energy` | `Energy` (custom) | — |
| **imu_node** | `/imu` | `sensor_msgs/Imu` | — |
| **teleop_twist_joy** | `/joy` | `sensor_msgs/Joy` | — |
| **distance_node** | `/ultrasound_data` | `Distance` (custom) | — |
| **car_control_node** | — | — | `/joy` |

### Descripción de nodos

- **camera_node:** Captura imágenes con OpenCV y las publica a 5 Hz (0.2s). Usa `CvBridge` para convertir a formato ROS2 (`Image`).
- **energy_node:** Lee voltaje de 3 celdas (`INA3221`) y corriente (`INA226`) por I2C. Publica en `/energy` cada segundo.
- **imu_node:** Lee aceleración y velocidad angular del `MPU6050`. Publica en `/imu` a 2 Hz.
- **teleop_twist_joy:** Nodo del paquete estándar de ROS2. Publica datos del mando PS3 en `/joy`.
- **distance_node:** Lee 3× HC-SR04 (izquierda, centro, derecha) y KY-032 (emergencia). Publica en `/ultrasound_data` a 10 Hz.
- **car_control_node:** Interpreta datos del mando PS3 para controlar velocidad y dirección del robot.

### Mensajes personalizados

Definidos en `src/messages_pkg/msg/`:

**Distance.msg:**
```
float32 left_distance
float32 right_distance
float32 center_distance
bool emergency_stop
```

**Energy.msg:**
```
float32 voltage_battery_1
float32 voltage_battery_2
float32 voltage_battery_3
float32 current
```

### Estructura del repositorio

| Directorio/Archivo | Contenido |
|---|---|
| `.venv/` | Entorno virtual Python3 con dependencias |
| `sixpair/` | Script de configuración del mando PS3 |
| `pruebas/` | Scripts del benchmarking de sensores |
| `src/` | Código de nodos ROS2 (paquetes) |
| `launch.sh` | Script para lanzar todos los nodos |
| `setup.sh` | Variables de entorno y configuración |

### Paquetes ROS2

1. **messages_pkg** — Mensajes personalizados (`Distance`, `Energy`)
2. **robocar_pkg** — Todos los nodos del proyecto
   - `lib/` — Librerías de drivers de hardware
   - `robocar_pkg/` — Archivos Python de los nodos
   - `setup.py` — Entry points de los nodos ejecutables
3. **teleop_twist_joy** — Submodule Git del paquete estándar de ROS2

### Construcción y ejecución

```bash
# Dentro del directorio src/
colcon build
source install/setup.sh

# Lanzar un nodo individual
ros2 run robocar_pkg camera_node

# Lanzar todos los nodos
bash launch.sh
```

### Servicio del sistema

Para que los nodos se lancen automáticamente al encender la Raspberry:

```ini
# /etc/systemd/system/robocar.service
[Service]
ExecStart=/home/lab/robocar/launch.sh
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable robocar.service
```

---

## Panel de Control (Node-RED)

### ¿Por qué Node-RED?

Node-RED es una herramienta de programación visual sobre Node.js, orientada a IoT. Ventajas:
- Interfaz visual intuitiva y sencilla
- Escalabilidad para usos complejos (optimización de rendimiento, detección anticipada de fallas)
- Amplia gama de nodos disponibles

### Interconexión ROS2 – Node-RED

ROS2 se comunica con Node-RED mediante **rclNodejs**, la implementación JavaScript de la ROS Client Library (al mismo nivel que rclPy para Python y rclCPP para C++).

**Primer intento:** Integration Service de eProsima → falló por insuficiencia de RAM (4GB) al compilar.

**Solución adoptada:** Plugin **EduArt-Robotik/edu_nodered_ros2_plugin**, más ligero y compatible con la Raspberry Pi. Se ejecutan los comandos del Dockerfile directamente en la RPi (sin Docker).

### Instalación

```bash
npm install -g --unsafe-perm node-red rclnodejs cron
cd /home/lab/edu_nodered_ros2_plugin
npm install -g .
```

Para mensajes custom, regenerar desde `/usr/lib/node_modules/rclnodejs/scripts`:
```bash
sudo su
source /opt/ros/iron/setup.sh
source /home/ros2/robocar/src/install/setup.sh
npm run generate-messages
```

### Dashboard

El panel de control muestra datos en tiempo real de los sensores. Los flujos se definen en `flows.json`.

#### Diagrama de Batería

Suscripción al topic `/energy` para mostrar:
- **Carga de baterías** (porcentaje calculado a partir del voltaje)
- **Potencia consumida** (W)
- **Salud de las baterías** (diferencia de potencial entre celdas → indica equilibrio del BMS)

> Nota: Si se alimenta con fuente externa, la potencia aparece negativa (no circula corriente desde las baterías).

#### Diagrama de Cámara

Visualización en tiempo real de los frames de la cámara (con retardo de algunos segundos).

#### Diagrama de Monitoreo Raspberry

Monitoreo en tiempo real del estado de la Raspberry Pi (CPU, temperatura, memoria, etc.).
