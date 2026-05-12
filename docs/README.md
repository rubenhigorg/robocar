# Documentación del Proyecto Robocar

Proyecto de robot coche autónomo desarrollado como Proyecto de Fin de Grado en la UPM, utilizando componentes comerciales de bajo coste, ROS2, visión artificial y sensores diversos.

## Trabajos Académicos

| Trabajo | Descripción | Autores | Curso |
|---|---|---|---|
| [**TFG 1: Diseño y Construcción**](tfg1-construccion/README.md) | Construcción completa del robot: hardware, sensores, electrónica, software ROS2 y panel de control Node-RED | Kento Reinoso, Rubén Higuera | 2023/24 |
| [**TFG 2: Seguimiento de Carril**](tfg2-lane-following/README.md) | Sistema de lane-following con OpenCV, Transformada de Hough, Filtro de Kalman y control PID | Rubén Higuera | 2023/24 |
| [**TFM** (en desarrollo)](tfm/README.md) | Extensión con LIDAR | Rubén Higuera | — |

## Índice Detallado

### TFG 1 — Diseño y Construcción de Robocar

- [Resumen y objetivos](tfg1-construccion/README.md)
- [Hardware: Actuadores, sensores y benchmarking](tfg1-construccion/hardware.md)
- [Electrónica: Alimentación y monitorización](tfg1-construccion/electronica.md)
- [Construcción: Montaje, cableado y piezas 3D](tfg1-construccion/construccion.md)
- [Software: ROS2 y Node-RED](tfg1-construccion/software.md)
- [📄 Memoria original (PDF)](tfg1-construccion/TFG_1.pdf)

### TFG 2 — Seguimiento de Carril

- [Resumen y objetivos](tfg2-lane-following/README.md)
- [Detección de carril: Pipeline de visión artificial](tfg2-lane-following/deteccion-carril.md)
- [Sistema de control: Filtro de Kalman y PID](tfg2-lane-following/sistema-control.md)
- [Modelo del sistema: Robot y entorno](tfg2-lane-following/modelo-sistema.md)
- [📄 Memoria original (PDF)](tfg2-lane-following/TFG_2.pdf)

## Estructura del Repositorio

```
docs/
├── README.md                           ← Estás aquí
├── tfg1-construccion/
│   ├── README.md                       # Resumen TFG1
│   ├── TFG_1.pdf                       # Memoria original
│   ├── hardware.md                     # Actuadores, sensores, benchmarking
│   ├── electronica.md                  # Baterías, alimentación, monitorización
│   ├── construccion.md                 # Montaje, piezas 3D, cableado
│   └── software.md                     # ROS2, Node-RED
├── tfg2-lane-following/
│   ├── README.md                       # Resumen TFG2
│   ├── TFG_2.pdf                       # Memoria original
│   ├── deteccion-carril.md             # Pipeline OpenCV
│   ├── sistema-control.md              # Kalman, PID
│   └── modelo-sistema.md              # Modelo robot + entorno
└── tfm/
    └── README.md                       # Placeholder TFM
```
