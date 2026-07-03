# Roadmap de implementación del TFM

[← Volver al TFM](README.md)

Este documento traduce las **cinco fases** de la metodología (Cap. 3 de la memoria) en un
plan técnico **capa a capa**, marcando qué existe ya, qué falta y **dónde están los riesgos
que la memoria no detalla**. Es el documento de trabajo para las **Entregas 2 y 3**
(Cap. 4 *Desarrollo específico de la contribución* y Cap. 5 *Conclusiones*).

!!! tip "Estado vivo del roadmap → [roadmap.iawiki.app](https://roadmap.iawiki.app)"
    El **estado actualizado** de cada tarea (pendiente/en curso/hecho, asignaciones e
    historial) se mantiene en el **[tablero web compartido](https://roadmap.iawiki.app)**
    (código en `tools/roadmap-web/`). Este documento recoge el **plan conceptual**: capas,
    hitos, dependencias y decisiones — lo que no cambia semana a semana.

!!! info "Estado global (a jul 2026)"
    **Entrega 1 completada** (Cap. 1-3: problema, estado del arte, objetivos y metodología).
    Implementación **en curso**: hito **0.1 (migración a Humble) completado** ✅ y
    **0.2 (puente `/cmd_vel`) en curso** 🔵. Antes del arranque, lo único disponible era la
    validación funcional del RPLidar C1 fuera de ROS2 (`pruebas/rplidar/`).

Leyenda de estado: ✅ hecho · 🟡 parcial · ⬜ pendiente

## 1. Diagrama conceptual por capas

La solución se organiza en cuatro capas. Las tres capas superiores son las que describe la
memoria (Percepción, Navegación, Interfaz natural); la **Capa 0** recoge los fundamentos ROS2
(URDF/TF, odometría y puente de actuación) que la memoria da por supuestos pero que hay que
construir explícitamente y concentran el mayor riesgo del proyecto.

```mermaid
flowchart TB
    user["👤 Usuario · lenguaje natural"]

    subgraph L3["Capa 3 — Interfaz natural (LLM + MCP)"]
      direction TB
      llm["LLM · Claude API<br/>razonamiento + tool use"]
      mcp["MCP Server · FastMCP<br/>navigate_to · get_current_location<br/>list_known_places · stop_navigation"]
    end

    subgraph L2["Capa 2 — Navegación (Nav2)"]
      direction TB
      sem["Resolución semántica<br/>SQLite: lugar → coordenada"]
      nav2["Nav2<br/>BT Navigator · planner global · controller (TEB)<br/>costmaps · AMCL"]
    end

    subgraph L1["Capa 1 — Percepción (SLAM)"]
      direction TB
      scan["/scan · rplidar_ros"]
      carto["Cartographer 2D<br/>→ /map + trayectoria"]
    end

    subgraph L0["Capa 0 — Fundamentos ROS2 (riesgo principal)"]
      direction TB
      tf["URDF + árbol TF<br/>base_link · laser"]
      odom["Odometría<br/>encoders + IMU"]
      bridge["Puente /cmd_vel → PCA9685<br/>(cinemática Ackermann)"]
    end

    hw["🔧 Hardware · RPLidar C1 · ESC/motores · servo dirección"]

    user --> llm
    llm <-->|MCP tools| mcp
    mcp -->|acción NavigateToPose| nav2
    sem --> nav2
    scan --> carto
    carto -->|/map + tf map→odom| nav2
    tf --> carto
    tf --> nav2
    odom -->|tf odom→base_link| carto
    odom --> nav2
    nav2 -->|/cmd_vel| bridge
    bridge --> hw
    hw --> scan
    hw --> odom
```

!!! note "Cómo leer el diagrama"
    El flujo de **control** baja de arriba abajo (usuario → LLM → MCP → Nav2 → hardware) y el
    flujo de **percepción** sube (hardware → `/scan` → Cartographer → Nav2). La Capa 0 sostiene
    a las dos: sin un TF y una odometría coherentes, ni Cartographer ni Nav2 funcionan, y sin el
    puente `/cmd_vel → PCA9685` la salida de Nav2 no llega a las ruedas.

## 2. Roadmap por capas

### Capa 0 — Fundamentos ROS2 *(pre-requisito, no explícito en la memoria)*

Antes de SLAM hay que resolver lo que la metodología da por hecho. La explicación conceptual
detallada (Ackermann, URDF/TF, odometría y por qué es el riesgo principal) está en
[Fundamentos ROS2](fundamentos.md).

!!! abstract "Estado de la plataforma (Raspberry Pi `robocar.local`, user `lab`) — jul 2026"
    - **Ubuntu 22.04.4 LTS**, Python 3.10.12. ROS2 **Iron** instalado; **Humble** confirmado
      instalable por apt (`ros-humble-navigation2` disponible).
    - **Stack del TFM sin instalar**: no hay Nav2, Cartographer, rplidar_ros ni robot_localization
      (solo `joy`). Partimos de cero en navegación → bajo coste de migrar a Humble.
    - Workspace en `/home/lab/robocar`, rama **TFG_2** (por detrás de `main`).
    - `robocar.service` (systemd, `User=lab` → `launch.sh`) existe y está **disabled**.
    - ⚠️ **LIDAR no conectado** ahora mismo (sin `/dev/ttyUSB*`). ⚠️ Disco al **85%** (4.2 GB libres).

Plan incremental de hitos (cada uno con una validación testable):

| Hito | Objetivo | Cómo se valida | Decisión |
|---|---|---|---|
| **0.1** ✅ | **Migrar a Humble**: instalar `ros-humble-ros-base` + deps, recompilar workspace (`robocar_pkg`, `messages_pkg`, `teleop_twist_joy`), limpiar el entry point `controller_node` colgante; purgar Iron tras validar | `colcon build` limpio y nodos TFG arrancan en Humble | **D1 ✔ Humble** |
| **0.2** 🔵 | **Puente `/cmd_vel` → PCA9685** (Ackermann): `angular.z`→servo dirección (canal 2), `linear.x`→ESC (canales 0/1); calibrar velocidad máx., ángulo de dirección máx. y *wheelbase*. Refactor del modo autónomo actual de `car_control_node` | **Conducir el coche con el mando** vía `/cmd_vel` (teleop_twist_joy ya lo emite) | D4 |
| **0.3** | **URDF + TF**: `xacro` con `base_link`, `laser` (offset del montaje), `imu_link` y ruedas; `robot_state_publisher` + transforms estáticos | Árbol TF coherente en RViz (`base_link → laser`) | — |
| **0.4** | **Odometría**: con D2=A no se monta odom de ruedas; se deja a Cartographer estimar la pose por *scan-matching*. Reservado el nodo encoder + modelo-bicicleta para la opción B | Se valida en la Capa 1 (pose estable en Cartographer) | **D2 ✔ A** |
| **0.5** | **Sanear `/imu`**: añadir `header` (timestamp + `frame_id`) y covarianzas a `accelerometer_node` | `/imu` válido para `robot_localization` (solo crítico si se migra a D2=B) | (D2) |

!!! warning "Cinemática Ackermann"
    Robocar **no es un robot diferencial**: dirige con un servo (tipo coche). Esto afecta al
    puente de actuación y a la elección de controlador local en la Capa 2. Es la diferencia
    conceptual más importante frente a los tutoriales estándar de Nav2 (pensados para
    TurtleBot diferencial).

!!! tip "Victoria temprana en 0.2"
    El `launch.sh` ya arranca `teleop_twist_joy`, que publica `/cmd_vel` desde el mando, pero hoy
    `car_control_node` lee `/joy` en crudo y ese `/cmd_vel` se ignora. Reaprovecharlo permite
    **validar el puente Ackermann con el mando antes de que exista Nav2**. Con 0.1 + 0.2 + 0.3
    hechos, la Capa 1 (SLAM) puede arrancar.

### Capa 1 — Percepción / SLAM *(Fase 1 · 3-4 semanas)*

- [ ] 🟡 **Sensor validado** a nivel hardware fuera de ROS2 (`pruebas/rplidar/`) — reutilizable como referencia.
- [ ] ⬜ **`rplidar_ros`** integrado publicando `/scan` (`sensor_msgs/LaserScan`) dentro de ROS2.
- [ ] ⬜ **Cartographer 2D** configurado (`.lua`) y ajustado a Raspberry Pi (resolución y frecuencia de optimización contenidas).
- [ ] ⬜ **Mapa del entorno** construido por teleoperación (mando PS3) y guardado (`.pgm` + `.yaml`).
- [ ] ⬜ **Base de datos SQLite** de lugares semánticos (nombre → coordenada en el mapa; ≥ 3 lugares).

!!! success "Puerta de validación — OE1"
    Mapa coherente y estable + localización reproducible con **error < 10 cm**.

### Capa 2 — Navegación *(Fase 2 · 3-4 semanas)*

- [ ] ⬜ **Nav2** configurado: BT Navigator, planner global (NavFn/Smac), costmaps (static + inflation + obstacle) y AMCL.
- [ ] ⬜ **Controlador local Ackermann**: **TEB** (o Regulated Pure Pursuit / MPPI), **no** el DWB diferencial (ver [Decisión D3](#3-decisiones-de-diseno)).
- [ ] ⬜ **Servicio de resolución semántica** (lee la SQLite: nombre de lugar → `PoseStamped`).
- [ ] ⬜ **Navegación punto a punto** validada entre waypoints en entorno controlado.

!!! success "Puerta de validación — OE2"
    **Tasa de éxito > 90 %** (≥ 20 ensayos, destino dentro de radio de 20 cm).

### Capa 3 — Interfaz natural / LLM + MCP *(Fases 3-4 · 4-6 semanas)*

- [ ] ⬜ **MCP Server** en Python con **FastMCP** y las 4 herramientas: `navigate_to()`, `get_current_location()`, `list_known_places()`, `stop_navigation()`.
- [ ] ⬜ **Cliente de acción `rclpy`** contra `NavigateToPose` (envío de meta, feedback, éxito/fallo/cancelación).
- [ ] ⬜ **Host + Claude API**: system prompt del asistente de navegación y bucle conversacional con *tool use*.

!!! success "Puertas de validación — OE3 / OE4"
    Herramientas invocables manualmente con comportamiento correcto (OE3) y **pipeline
    end-to-end** desde texto del usuario hasta movimiento del robot (OE4).

!!! tip "Se puede adelantar"
    El MCP Server puede desarrollarse y probarse contra un **Nav2 simulado (mock)** sin esperar
    a que la Capa 2 esté cerrada, para no bloquear el trabajo de la interfaz.

### Capa 4 — Validación y cierre *(Fase 5 · 2-3 semanas)*

- [ ] ⬜ **Batería de pruebas** end-to-end: comandos simples, secuencias compuestas y casos de error.
- [ ] ⬜ **Toma de métricas** (OE1-OE4) y refinamiento de casos de fallo.
- [ ] ⬜ **Redacción** del Cap. 4 (desarrollo) y Cap. 5 (conclusiones y líneas futuras) + Resumen/Abstract.

## 3. Decisiones de diseño

| ID | Decisión | Estado | Detalle |
|---|---|---|---|
| **D1** | Distro ROS2 | ✅ **Humble** | El stack del TFM no está instalado bajo ninguna distro, así que migrar a Humble (LTS, lo que dice la memoria) tiene coste casi nulo. Instalar junto a Iron y purgar Iron tras validar. Alinear el README (dice Iron). |
| **D2** | Odometría/localización | ✅ **Opción A ahora** | Empezar con la pose por *scan-matching* de Cartographer (sin odometría de ruedas). Migrar a **B** (encoders + IMU con `robot_localization` EKF + AMCL) **solo si** no se cumple OE1 (< 10 cm); en ese caso, documentarla en el Cap. 4 (no está en la memoria). |
| **D3** | Controlador local Nav2 | 🟡 Previsto | **TEB** (o Regulated Pure Pursuit / MPPI) por la cinemática Ackermann; **no** el DWB diferencial. La propia memoria lo señala. Se cierra en la Capa 2. |
| **D4** | Puente de actuación | 🟡 Previsto | Refactor del modo autónomo de `car_control_node` (o nodo nuevo) que traduzca `/cmd_vel` (`Twist`) a ángulo de servo (canal 2) + throttle ESC (canales 0/1) respetando límites Ackermann. Se implementa en el hito 0.2. |

## 4. Camino crítico y riesgos

!!! danger "Dónde se atascan los TFM de robótica"
    El riesgo **no está en el LLM ni en el MCP** (es la parte más acotada y controlable), sino
    en la **Capa 0-2**: TF, odometría y el puente Ackermann. Ahí conviene invertir el esfuerzo.

- **Secuencialidad estricta hasta la Capa 3**: sin `/scan` en ROS2 no hay mapa; sin mapa no hay
  Nav2; sin Nav2 no hay acción que el MCP invoque. La única paralelización razonable es
  adelantar el MCP Server contra un Nav2 *mock*.
- **Cómputo en la Pi 4 (4 GB)**: `rplidar_ros` + Cartographer + Nav2 juntos van justos pero son
  viables (equivalente a TurtleBot3). El LLM corre **fuera** de la Pi vía Claude API, así que no
  añade carga local.
- **Odometría Ackermann**: es la incógnita técnica principal (Decisión D2) y afecta directamente
  a OE1 y OE2.

## 5. Correspondencia fases ↔ capas ↔ objetivos

| Fase (memoria) | Capa (este roadmap) | Objetivo | Métrica |
|---|---|---|---|
| Fase 1 · SLAM y mapa semántico | Capa 0 + Capa 1 | OE1 | Error localización < 10 cm |
| Fase 2 · Navegación con Nav2 | Capa 2 | OE2 | Éxito navegación > 90 % |
| Fase 3 · MCP Server | Capa 3 | OE3 | 4 tools operativas |
| Fase 4 · Integración con LLM | Capa 3 | OE4 | Interpretación NL > 85 % |
| Fase 5 · Pruebas y evaluación | Capa 4 | OE1-OE4 | + latencia mediana < 5 s |

## 6. Pendientes de la memoria *(pulido, no urgente)*

- **Distro descuadrada**: el repo/README indica **Iron** y la memoria **Humble** (Decisión D1).
- **Referencias de los TFG previos**: en la bibliografía la autoría/año de los dos TFG aparece
  cruzada respecto al cuerpo del texto (construcción como 2023 individual, lane-following como
  2024 a dos autores; en el cuerpo es al revés). Revisar antes de la entrega final.
- **Odometría/EKF**: si se adopta la opción D2-B, documentarla en el Cap. 4.
