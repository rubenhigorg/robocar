# TFG 1: Diseño y Construcción de Robocar

> **Proyecto de Fin de Grado** — Ingeniería de Computadores / Tecnologías de la Sociedad de la Información  
> **Autores:** Kento Reinoso Hayashi, Rubén Higuera Castillo  
> **Curso:** 2023/2024  
> 📄 [Memoria original (PDF)](TFG_1.pdf)

## Introducción

Este proyecto se centra en el diseño y construcción de un robot coche autónomo utilizando componentes comerciales de coste contenido, con el objetivo de alcanzar la máxima autonomía posible. Abarca desde la selección de sensores, la arquitectura del sistema, y la construcción física, hasta la implementación del software de control y un panel de monitorización en tiempo real.

## Marco Teórico

La conducción autónoma se define según la SAE en 6 niveles (0–5), desde totalmente manual hasta totalmente autónomo. Los vehículos autónomos combinan múltiples tipos de sensores (RADAR, LIDAR, cámaras, ultrasonidos, IMU, GNSS) con algoritmos de procesamiento para percibir el entorno y actuar sobre él. La arquitectura funcional se divide en tres capas: **Percepción**, **Planificación y Decisión**, y **Control**.

Este proyecto se sitúa en un nivel básico de autonomía, integrando percepción mediante sensores de distancia y cámara, y control directo de actuadores.

## Objetivos

- Implementar un sistema de baterías capaz de soportar la carga del coche
- Demostrar las virtudes de sensores concretos mediante un benchmarking
- Incorporar un entorno ROS2 para la recolección y procesamiento de datos
- **Objetivo final nº1:** Montaje completo del coche
- **Objetivo final nº2:** Panel de control con datos en tiempo real de los sensores

## Metodología

Se adopta un **desarrollo en espiral incremental**: ciclos de ~2 semanas con definición de objetivos, análisis de riesgos, desarrollo, integración, pruebas y evaluación. Se utilizan diagramas de GANTT para la planificación de cada iteración. Este enfoque resulta especialmente efectivo para proyectos que combinan hardware y software, ya que permite la detección temprana de errores.

## Inventario

| Componente | Precio |
|---|---|
| Chasis Robot DFRobot GPX: Asurada | 110€ |
| Raspberry Pi 4 4GB | 80€ |
| Sensores VL53L0X, VL53L1X, VL6180X, HC-SR04, GP2YE03, KY-032 | ~20€ |
| RPi Camera Rev 1.3 | 10€ |
| MPU6050 | 12€ |
| PCA9685 | 8€ |
| Display Batería 3S | 1€ |
| 6× celdas iones de litio | Reciclado |
| PCBs, cables, resistencias, soldador | ~52€ |
| **Total** | **~293€** |

> El chasis incluye los dos motores ESC, un servomotor de dirección y un mástil para la cámara.

## Documentación Detallada

| Documento | Contenido |
|---|---|
| [Hardware: Actuadores, Sensores y Benchmarking](hardware.md) | Actuadores (ESC, servo), sensores de distancia, cámara, IMU, benchmarking completo |
| [Electrónica: Alimentación y Monitorización](electronica.md) | Baterías (2p3s), BMS, sensores INA3221/INA226, BUCK, distribución de alimentación |
| [Construcción: Montaje y Piezas 3D](construccion.md) | Raspberry Pi, estrategia de sensores, cableado, piezas 3D, problemáticas |
| [Software: ROS2 y Node-RED](software.md) | Entorno de desarrollo, nodos ROS2, panel de control Node-RED |

## Conclusiones

- Es posible alcanzar un producto hardware maduro con potencial de autonomía usando componentes comerciales y presupuesto contenido (~293€)
- La metodología en espiral incremental es efectiva para sistemas hardware+software
- El benchmarking demostró que los sensores económicos proporcionan resultados precisos y fiables (errores <20%), y que la luz ambiental no afecta significativamente su desempeño
- El sensor HC-SR04, uno de los más económicos, demostró las mejores características generales
- Las predicciones de tiempo para procesos de construcción física son sistemáticamente optimistas — es frecuente repetir, reconstruir y testear componentes

### Líneas Futuras

- Incorporación de sensores adicionales o más avanzados (LIDAR)
- Algoritmos de inteligencia artificial para mejorar la toma de decisiones
- Hardware de procesamiento más potente (Nvidia Jetson Nano) para procesamiento de imagen en tiempo real

## Referencias

- [Datasheet VL53L0X](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- [Tutorial HC-SR04 en Raspberry Pi](https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi)
- [Sensor GP2Y0E03](https://www.luisllamas.es/medir-distancia-con-arduino-y-el-sensor-gp2y0e03/)
- [Datasheet KY-032](https://www.alldatasheet.es/datasheet-pdf/pdf/1284503/JOY-IT/KY-032.html)
