# Recursos visuales

Esta página recoge la **clasificación inicial de las imágenes extraídas** de las tres memorias del proyecto. El objetivo es doble:

1. localizar rápido diagramas, fotos y capturas para enriquecer la documentación actual;
2. preparar una selección posterior para el `README.md` y la futura landing visual.

En todos los casos se ha mantenido el nombre original del archivo (`*_pXX_YY.ext`) para conservar la referencia a la **página del PDF de origen**.

## Criterio de clasificación

- La organización sigue **bloques temáticos reutilizables** dentro de `docs/`, no solo el tipo de imagen.
- Se han agrupado juntos los recursos que previsiblemente acabarán en la misma página o sección.
- La clasificación es deliberadamente práctica: prioriza la **reutilización documental** sobre una taxonomía académica más rígida.

## Inventario global

| Fuente | Archivos | Carpeta base |
|---|---:|---|
| **TFG 1** | 86 | `assets/images/tfg1/` |
| **TFG 2** | 70 | `assets/images/tfg2/` |
| **TFM** | 6 | `assets/images/tfm/` |

## TFG 1 — Construcción, electrónica y base software

| Carpeta | Alcance | Páginas PDF | Archivos | Reutilización prevista |
|---|---|---|---:|---|
| `assets/images/tfg1/contexto/` | Esquema general, autonomía SAE, sensorización, arquitectura funcional, GANTT, entorno de trabajo | 1, 5-14 | 8 | Introducción, cronología del proyecto, futura landing |
| `assets/images/tfg1/hardware-sensores/` | Actuadores, sensores, scripts de prueba y benchmarking | 16-34 | 24 | `hardware.md` |
| `assets/images/tfg1/electronica-bateria/` | BMS, INAs, esquemas eléctricos, montaje y pruebas de batería | 35-45 | 15 | `electronica.md` |
| `assets/images/tfg1/montaje-componentes/` | Piezas 3D, integración física, componentes auxiliares y foto final del robot | 48-55, 74 | 18 | `construccion.md`, README, landing |
| `assets/images/tfg1/software-dashboard/` | ROS2, paquetes, despliegue, Node-RED y paneles de control | 57-71 | 21 | `software.md` |

## TFG 2 — Detección de carril y control

| Carpeta | Alcance | Páginas PDF | Archivos | Reutilización prevista |
|---|---|---|---:|---|
| `assets/images/tfg2/contexto/` | ADAS, arquitectura de vehículo autónomo, taxonomías y circuito de pruebas | 1-18 | 12 | Resumen del TFG2, contexto del algoritmo |
| `assets/images/tfg2/control-kalman-pid/` | Hough, Kalman, PID y diagramas de control | 21-29 | 11 | `sistema-control.md` |
| `assets/images/tfg2/modelo-geometria/` | ROI, modelo del carril, geometría del robot y análisis de trayectoria | 30-40 | 14 | `modelo-sistema.md` |
| `assets/images/tfg2/integracion-hardware/` | Cámara, sensor de velocidad, diagramas de estado/ROS y fotos del sistema | 41-42, 52-53, 67-68 | 9 | Resumen del TFG2 y secciones de integración |
| `assets/images/tfg2/pipeline-vision/` | Código y etapas del pipeline de visión artificial | 43-49, 51 | 11 | `deteccion-carril.md` |
| `assets/images/tfg2/resultados-validacion/` | Trazado del circuito y frames de resultados en rectas y curvas | 54, 56-60 | 13 | `deteccion-carril.md`, futura sección de resultados |

## TFM — Evolución hacia navegación semántica

| Carpeta | Alcance | Páginas PDF | Archivos | Reutilización prevista |
|---|---|---|---:|---|
| `assets/images/tfm/contexto-arquitectura/` | Punto de partida de Robocar y arquitectura por capas del TFM | 1-2, 11 | 3 | `tfm/README.md`, landing |
| `assets/images/tfm/slam/` | Relación entre SLAM y Nav2 | 13 | 1 | `tfm/slam.md` |
| `assets/images/tfm/navegacion/` | Arquitectura interna del stack Nav2 | 17 | 1 | `tfm/navegacion.md` |
| `assets/images/tfm/llm-mcp/` | Flujo completo del comando en lenguaje natural | 22 | 1 | `tfm/llm-mcp.md` |

## Qué carpetas conviene atacar primero

Si el siguiente paso es **empezar a enriquecer páginas concretas**, el mejor orden es:

1. `assets/images/tfg1/montaje-componentes/` y `assets/images/tfg1/electronica-bateria/`
2. `assets/images/tfg2/modelo-geometria/`, `assets/images/tfg2/pipeline-vision/` y `assets/images/tfg2/resultados-validacion/`
3. `assets/images/tfm/contexto-arquitectura/`, `assets/images/tfm/slam/`, `assets/images/tfm/navegacion/` y `assets/images/tfm/llm-mcp/`

Con esta base, la integración posterior ya puede hacerse con criterio: **una imagen representativa por página**, después galerías cortas solo donde realmente aporten contexto técnico.
