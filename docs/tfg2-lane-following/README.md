# TFG 2: Diseño e Implementación de Seguimiento de Carril

> **Proyecto de Fin de Grado** — Ingeniería de Computadores  
> **Autor:** Rubén Higuera Castillo  
> **Curso:** 2023/2024  
> 📄 [Memoria original (PDF)](TFG_2.pdf)

## Introducción

Este TFG continúa el trabajo de ["Diseño y Construcción de Robocar"](../tfg1-construccion/README.md), cuyo resultado fue un robot físico dotado de sensores y controlado mediante ROS2. El objetivo es implementar un sistema de **seguimiento de carril** utilizando tecnologías de asistencia a la conducción (ADAs): detección por visión artificial, filtrado de Kalman y control PID.

Todo el código se encuentra en la rama `TFG_2` del repositorio: [github.com/rubenhigorg/robocar/tree/TFG_2](https://github.com/rubenhigorg/robocar/tree/TFG_2)

## Marco Teórico

El seguimiento de carril opera en un bucle cerrado con las siguientes etapas:

1. **Sensores** → Captura de datos del entorno (cámara, IMU, GPS...)
2. **Extracción de características** → Detección de bordes del carril
3. **Post-procesamiento** → Estimación de líneas (Transformada de Hough)
4. **Seguimiento** → Suavizado y predicción (Filtro de Kalman)
5. **Control** → Corrección de dirección (PID)

Los enfoques para detección de carriles se clasifican en:
- **Basado en características:** Bordes, color, brillo, textura. Insensible a formas pero sensible a iluminación.
- **Basado en modelos:** Modelos globales de carretera. Robusto ante iluminación pero sensible a formas.
- **Basado en aprendizaje:** Redes neuronales y reinforcement learning. Requiere entrenamiento extenso.

## Objetivos

Implementar un sistema de seguimiento de carril para Robocar bajo las siguientes condiciones:

- Carril de ancho constante, delimitado por línea roja
- Sin curvas muy pronunciadas (ángulo máximo de giro: 30°)
- Velocidad constante y baja (~18 cm/s)
- Procesamiento sobre Raspberry Pi 4B con ROS2

## Tecnologías Seleccionadas

| Componente | Selección | Justificación |
|---|---|---|
| Sensor | Cámara | OpenCV es casi un estándar |
| Extracción de características | Detección de color rojo | Detección fiable |
| Post-procesamiento | Transformada de Hough | Estándar en detección de rectas |
| Seguimiento | Filtro de Kalman | Uso generalizado, eficiente |
| Modelo de carril | Lineal (campo cercano) | Sencillez |
| Posición respecto al carril | Offset al final de ROI | Baja velocidad, sencillez |
| Control de dirección | Promedio lineal de líneas detectadas | Robustez ante pérdida parcial |
| Gestión de control | PID | Eficiente, ampliamente usado |

## Documentación Detallada

| Documento | Contenido |
|---|---|
| [Detección de Carril](deteccion-carril.md) | Pipeline OpenCV completo: filtro de color, Canny, ROI, Hough, escenarios de detección |
| [Sistema de Control](sistema-control.md) | Filtro de Kalman para seguimiento, control PID, cálculo de error y ángulo de giro |
| [Modelo del Sistema](modelo-sistema.md) | Modelo geométrico del robot, ROI, cámara, cálculos de trayectoria |

## Cambios de Hardware

### Cámara

La cámara original (RPi Camera Rev 1.3 clónica) presentaba **baja velocidad de obturación**: las imágenes salían movidas cuando el robot se desplazaba. Se sustituyó por una **webcam NexiGo** (USB):
- Full HD 1080p @ 60fps
- Balance de blancos y exposición automáticos
- Buen rendimiento en condiciones de poca retroiluminación

### Sensor de velocidad

Se añadió un sensor en el eje de una rueda trasera basado en un **opto-acoplador**:
- Detecta impulsos de un LED que pasan por una rejilla
- El conteo lo realiza un **Arduino Nano**
- La información se envía a la RPi por **I2C** para integración en ROS2

## Integración en ROS2

Se crean/modifican los siguientes nodos:

- **processing_node** (nuevo): Recibe frames de `/camera_image`, procesa la detección de carriles, y publica el error de dirección en `/lane_info`
- **car_control_node** (modificado): Admite dos modos de operación:
  - **Manual:** Control vía joystick (`/joy`)
  - **Autónomo:** Sigue las correcciones de `/lane_info` a velocidad constante (18 cm/s)
  - **Cambio de modo:** Botón X del mando PS3

## Resultados

### Condiciones ideales
El sistema es capaz de identificar y seguir carriles con precisión razonable. En tramos rectos con iluminación uniforme, el robot se mantiene centrado con margen de error bajo.

### Dificultades
- **Iluminación variable:** En curvas y tramos con cambios abruptos de luz, la detección fue inconsistente
- **Curvas cerradas:** El circuito resultó estrecho para el ángulo de giro máximo (30°), haciendo que curvas "leves" requirieran giro máximo

### Papel del filtro de Kalman
El filtro de Kalman demostró ser crucial como **red de seguridad**: cuando el sistema no detectaba carriles (por iluminación o ángulo), las estimaciones de Kalman mantuvieron el seguimiento. Esto demuestra la **resiliencia** del sistema pero también su **dependencia de condiciones lumínicas adecuadas**.

## Conclusiones

- El sistema funciona correctamente bajo condiciones controladas de iluminación
- El filtro de Kalman compensa eficazmente las detecciones parciales o ausentes
- La sensibilidad a cambios de iluminación es la principal limitación
- Una evaluación comparativa con tecnologías alternativas (LIDAR, fusión de sensores, deep learning) sería necesaria para determinar la viabilidad en entornos reales

### Líneas Futuras

- **Mejor cámara:** Mayor resolución y rendimiento en baja luz
- **Nvidia Jetson Nano:** Procesamiento más potente para algoritmos avanzados (redes neuronales profundas)
- **Integración de sensores adicionales:** Usar los ultrasonidos y el sensor de emergencia para mejorar la percepción
- **Técnicas avanzadas de procesamiento de imagen** adaptables a variaciones de iluminación

## Bibliografía

1. Nguyen, T.B. "Evaluation of Lane Detection Algorithms based on an Embedded Platform", TU Chemnitz, 2017
2. Ulbrich, S. "Towards a Functional System Architecture for Automated Driving", 2017
3. McCall, J.C. & Trivedi, M.M. "Video-based lane estimation and tracking for driver assistance", IEEE, 2006
4. Waykole, S.S. et al. "Review on Lane Detection and Tracking Algorithms of ADAS", Sustainability, 2021
5. Lee, C. & Moon, J. "Robust Lane Detection and Tracking for Real-Time Applications", IEEE, 2018
6. Wang, P. & Chan, C. "A reinforcement learning based approach for automated lane change", IEEE, 2018
7. Saleem, H. "Steering Angle Prediction Techniques for Autonomous Ground Vehicles", IEEE Access
8. Yang, Z. "Accurate and robust vanishing point detection in unstructured road scenes", IEEE, 2019
9. AbdElrahman et al. "Vision-based road tracking of wheeled mobile robot", 2013
10. Snider, J.M. "Automatic Steering Methods for Autonomous Automobile Path Tracking", CMU, 2009
11. Reinoso, K. & Higuera, R. "Diseño y Construcción de Robocar", Madrid, 2024
12. Litman, T. "Autonomous Vehicle Implementation Predictions", Victoria Transport Policy Institute, 2022
