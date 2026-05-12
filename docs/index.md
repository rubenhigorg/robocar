---
hide:
  - navigation
  - toc
---

<div class="hero-split" markdown>
<div class="hero-text" markdown>


# Robocar

<p class="hero-deck">Un coche RC autónomo construido desde cero, desde las baterías y el chasis hasta algoritmos de visión artificial, SLAM y navegación inteligente.</p>

Diseñado, construido y programado como resultado de **dos Trabajos de Fin de Grado**
en la Universidad Politécnica de Madrid y un **Trabajo de Fin de Máster** en la UNIR.

[Explorar documentación](#evolucion-del-proyecto){ .md-button .md-button--primary }
[Ver en GitHub](https://github.com/rubenhigorg/robocar){ .md-button }

</div>
<div class="hero-image-wrapper" markdown>

![Robocar](assets/images/tfm/contexto-arquitectura/tfm_p02_00.png){ .hero-image }

</div>
</div>

---

## Evolución del proyecto { #evolucion-del-proyecto }

<div class="grid cards" markdown>

-   :material-wrench:{ .lg .middle } **TFG 1 — Diseño y Construcción**

    ---

    ![Construcción del robot](assets/images/tfg1/montaje-componentes/tfg1_p52_00.jpg){ .card-image }

    Chasis, electrónica, sensores, baterías, piezas 3D impresas, software ROS2 y panel de control Node-RED.

    **Coste total: ~293€**

    [:octicons-arrow-right-24: Ver documentación](tfg1-construccion/README.md)

-   :material-eye:{ .lg .middle } **TFG 2 — Seguimiento de Carril**

    ---

    ![Seguimiento de carril con Kalman](assets/images/tfg2/pipeline-vision/tfg2_p51_00.jpg){ .card-image }

    Lane-following con OpenCV: filtro de color, Canny, Hough, Filtro de Kalman y control PID.

    **Velocidad autónoma: 18 cm/s**

    [:octicons-arrow-right-24: Ver documentación](tfg2-lane-following/README.md)

-   :material-radar:{ .lg .middle } **TFM — Navegación Inteligente**

    ---

    ![Arquitectura del TFM](assets/images/tfm/contexto-arquitectura/tfm_p11_00.png){ .card-image }

    SLAM con RPLidar C1 + Cartographer, Nav2 para planificación de rutas, y control por lenguaje natural con LLM + MCP.

    **Estado: En desarrollo 🚧**

    [:octicons-arrow-right-24: Ver documentación](tfm/README.md)

</div>

---

## Arquitectura del Sistema

![Esquema general del proyecto](assets/images/Gemini_Generated_Image_9ct2959ct2959ct2.png){ .arch-image }

### Diagrama de Conexiones Hardware

<div class="diagram-legend" markdown>
:material-circle:{ .legend-i2c } I²C Bus 1 · :material-circle:{ .legend-gpio } GPIO · :material-circle:{ .legend-pwm } PWM / Servo · :material-circle:{ .legend-usb } USB · :material-circle:{ .legend-pwr } Alimentación
</div>

<div class="diagram-wrapper">
  <iframe src="robocar_diagram.html" class="hw-diagram" loading="lazy"></iframe>
</div>

---

## El robot en cifras

<div class="grid cards" markdown>

-   :material-currency-eur:{ .lg .middle } **~293€**

    ---

    Coste total con componentes comerciales de bajo coste y celdas de batería recicladas

-   :material-chip:{ .lg .middle } **Raspberry Pi 4**

    ---

    Ubuntu 22.04 LTS, ROS2 Iron, 4 GB RAM

-   :material-video:{ .lg .middle } **6 sensores**

    ---

    Cámara, 3× ultrasonidos HC-SR04, IMU MPU6050 y monitorización energética

-   :material-gamepad-variant:{ .lg .middle } **2 modos**

    ---

    Manual (joystick PS3) y autónomo (seguimiento de carril por visión artificial)

</div>

---

## Modos de conducción

=== "Manual"

    Control directo con mando **DualShock 3** (PS3) por Bluetooth.
    Los ejes del joystick controlan dirección y velocidad de forma independiente.

=== "Autónomo"

    El `processing_node` detecta los carriles de la pista mediante visión artificial
    y publica correcciones de dirección que el `car_control_node` aplica automáticamente
    a velocidad constante (18 cm/s).

> **Cambio de modo:** Botón **X** del mando PS3

---

## Autores

| Nombre | Contribución |
|---|---|
| **Rubén Higuera Castillo** | TFG 1, TFG 2, TFM |
| **Kento Reinoso** | TFG 1 |

---

<div class="footer-links" markdown>

[:material-file-document: Recursos visuales](recursos-visuales.md) · [:material-github: Repositorio](https://github.com/rubenhigorg/robocar) · [:material-school: UPM](https://www.upm.es)

</div>
