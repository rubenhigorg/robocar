# 🚗 Robocar

**Robot coche autónomo construido con componentes comerciales de bajo coste (~293€), capaz de seguimiento de carril mediante visión artificial.**

Funciona con **ROS2 Iron** sobre **Raspberry Pi 4**, integrando sensores ultrasónicos, IMU, monitorización energética y cámara con procesamiento OpenCV.

---

## 🎯 Qué es este proyecto

Robocar es el resultado de **dos Trabajos de Fin de Grado** y un **Trabajo de Fin de Máster** en la Universidad Politécnica de Madrid. Cubre desde la construcción mecánica y electrónica del robot hasta la implementación de algoritmos de visión artificial y control autónomo.

<div class="grid cards" markdown>

-   :material-wrench:{ .lg .middle } **TFG 1 — Diseño y Construcción**

    ---

    Hardware, sensores, electrónica, software ROS2 y panel de control Node-RED

    [:octicons-arrow-right-24: Ver documentación](tfg1-construccion/README.md)

-   :material-eye:{ .lg .middle } **TFG 2 — Seguimiento de Carril**

    ---

    Lane-following con OpenCV, Transformada de Hough, Filtro de Kalman y control PID

    [:octicons-arrow-right-24: Ver documentación](tfg2-lane-following/README.md)

-   :material-radar:{ .lg .middle } **TFM — Extensión con LIDAR**

    ---

    Ampliación del sistema con RPLidar C1 para percepción del entorno

    [:octicons-arrow-right-24: Ver documentación](tfm/README.md)

</div>

## 🏗️ Arquitectura del Sistema

| Nodo | Topic | Función |
|---|---|---|
| `camera_node` | `/camera_image` | Captura frames 640×480 a ~3 FPS |
| `processing_node` | `/lane_info` | Detecta carriles (OpenCV + Kalman + PID) |
| `car_control_node` | `/joy`, `/lane_info` | Controla motores y dirección |
| `distance_node` | `/ultrasound_data` | 3× HC-SR04 a 10 Hz |
| `energy_node` | `/energy` | Voltajes (INA3221) y corriente (INA226) |
| `accelerometer_node` | `/imu` | Acelerómetro + giroscopio (MPU6050) |

## 🎮 Modos de conducción

- **Manual:** Control directo con joystick PS3
- **Autónomo:** Seguimiento de carril por visión artificial
- **Cambio de modo:** Botón X del mando PS3

## 📊 Datos del proyecto

| | |
|---|---|
| **Coste total** | ~293€ |
| **Plataforma** | Raspberry Pi 4 (4GB) |
| **Framework** | ROS2 Iron |
| **Sensores** | Cámara, 3× ultrasonidos, IMU, monitorización energética |
| **Control** | PCA9685 (servos) + Filtro de Kalman + PID |

## 👤 Autores

| Nombre | Contribución |
|---|---|
| **Rubén Higuera Castillo** | TFG 1, TFG 2, TFM |
| **Kento Reinoso** | TFG 1 |
