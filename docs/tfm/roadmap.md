# Roadmap de implementación del TFM

[← Volver al TFM](README.md)

!!! tip "📊 El estado vivo del proyecto está en el tablero: [roadmap.iawiki.app](https://roadmap.iawiki.app)"
    Tareas, subtareas, dependencias, **Gantt auto-programado**, camino crítico e historial —
    todo se gestiona en el **[tablero web compartido](https://roadmap.iawiki.app)**
    (código en `tools/roadmap-web/`). Esta página recoge únicamente el **marco conceptual**
    que da contexto a la memoria: capas, decisiones de diseño y riesgos.

## Diagrama conceptual por capas

La solución se organiza en cuatro capas. Las tres superiores son las que describe la memoria
(Percepción, Navegación, Interfaz natural); la **Capa 0** recoge los fundamentos ROS2
(URDF/TF, odometría y puente de actuación) que la memoria da por supuestos y que concentran
el riesgo técnico — su explicación detallada está en [Fundamentos ROS2](fundamentos.md).

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

    subgraph L0["Capa 0 — Fundamentos ROS2"]
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

El **panel de control web** (`tools/car-panel/`, servido desde el propio vehículo) es
**transversal a todas las capas**: cada una aterriza visualmente en él (scan y sensores hoy;
mapa, navegación y chat LLM conforme avancen las capas). Actúa como mecanismo de observación
y pruebas de todo el sistema.

## Banco de simulación — preparatoria de la Capa 2 (Navegación)

Antes de cablear Nav2 + Cartographer sobre el hardware real, validamos la lógica de navegación
(seguimiento de trayectoria, evitación de obstáculos, maniobras Ackermann) en un **banco de
simulación** que corre en el propio vehículo, con las ruedas al aire. La **clave de diseño**:
el banco **habla exactamente las mismas interfaces que Nav** — mismos *topics*, tipos, *frames*
y restricciones cinemáticas — de modo que sustituir el banco por la pila real (mapa de
Cartographer + planificador/controlador de Nav2) sea un **_drop-in_**, sin reescribir nada
aguas arriba ni aguas abajo. Dicho de otro modo: **el banco tiene que responder a lo que Nav
va a ser**, no a un simulador ad-hoc que luego haya que tirar.

Componentes actuales del banco y a qué corresponden en la pila real:

| Banco (hoy) | Sustituye a (Capa 1-2) | Interfaz — **idéntica** en banco y en real |
|---|---|---|
| Mapa dibujado en web (**plantas de piso 100-200 m² con muebles**) → `sim_sensors_node` | El **`/map`** (OccupancyGrid) que producirá **Cartographer** (Capa 1) | el "mundo" que percibe el robot |
| `sim_sensors_node` (ray-cast del mapa desde la pose) | El **RPLidar C1** real (`rplidar_ros`) | **`/scan`** (`sensor_msgs/LaserScan`, frame `laser`/`base_link`) — lo consume la capa de obstáculos del *costmap* |
| **`sim_motion_node`** (integra `/cmd_vel` con el modelo de bicicleta) | El **robot físico + su odometría** (EKF encoder+IMU+dirección) en el suelo | **`/odometry/filtered`** + TF `odom→base_link` |
| Waypoints dibujados en web (`/plan_waypoints`) | El **objetivo** (`NavigateToPose` / `/goal_pose`) que fija Nav2 / el LLM | pose(s) objetivo |
| `trajectory_nav_node` (go-to-goal + evitación + k-turn) | El **planner global + controlador local (TEB)** de Nav2 | **`/cmd_vel`** (`geometry_msgs/Twist`) → `car_control` |

**La "planta" del banco (cómo se mueve el robot).** El banco corre en modo **simulación cinemática
pura**: `sim_motion_node` integra `/cmd_vel` con el modelo de bicicleta Ackermann
(ω = v·tan δ/L, con los **mismos** `L`, `tan_max`, `max_angular` que la odometría de dirección)
y publica `/odometry/filtered` + TF `odom→base_link` **sin depender de ruedas/encoder/IMU/EKF**.
Así el robot simulado gira con el **mismo radio mínimo real (R_min ≈ 0.93 m)** y dispara el
**k-turn** igual que en el suelo, pero de forma **reproducible y sin hardware** (validado: recto
0.3 m/s→0.61 m; arco a tope→37.7°, radio 0.93 m; lazo completo con `trajectory_nav`). El modo
alternativo **hardware-in-the-loop** (ruedas al aire + encoder/IMU/EKF reales, `bringupF`) queda
para validar la **cadena real de actuación y odometría** antes de bajar al suelo. En ambos, todo
lo demás (mapa, sensores, navegador, web) es idéntico.

Por eso las **plantas de piso** de la web no son decorativas: son el *stand-in* del mapa que
mañana dará el SLAM, con geometría realista para pisos de 100-200 m² (pasillos, puertas ~0.8 m,
muebles como obstáculos). Validar aquí que el coche recorre trayectorias correctas y esquiva
**respetando su radio de giro mínimo real (R_min ≈ 0.93 m → _k-turn_ en giros cerrados)**
de-risquea directamente el *tuning* de TEB en la Capa 2, porque el controlador de Nav2 tendrá
que respetar esa misma restricción Ackermann.

```mermaid
flowchart TB
    subgraph IFACE["Contrato Nav — mismas interfaces hoy (banco) y mañana (real)"]
      direction LR
      scanT["/scan"]
      odomT["/odometry/filtered + TF"]
      goalT["objetivo · waypoints / NavigateToPose"]
      cmdT["/cmd_vel"]
    end

    ss["sim_sensors_node<br/><i>banco (hoy)</i>"] -.->|hoy| scanT
    lidar["RPLidar + Cartographer<br/><i>real (mañana)</i>"] -.->|mañana| scanT

    scanT --> tn & nav2
    goalT --> tn & nav2
    odomT --> tn & nav2

    tn["trajectory_nav_node<br/><i>banco (hoy)</i>"] -.->|hoy| cmdT
    nav2["Nav2 · planner + TEB<br/><i>real (mañana)</i>"] -.->|mañana| cmdT

    cmdT --> cc["car_control → hardware"]
```

**Para que el banco sea un _drop-in_ fiel de Nav (convergencia pendiente):**

1. ✅ **HECHO** — Publicar el mapa dibujado también como **`/map` (`nav_msgs/OccupancyGrid`)**:
   `sim_map_grid_node` rasteriza los segmentos (`/sim_map`) a rejilla de ocupación (celdas
   pared=100, libre=0, 0.05 m/celda), QoS `transient_local` (latched) + republish 1 Hz. Alimenta
   la **capa estática del _costmap_** de Nav2 con el mismo mapa de banco. Pintado también en la web.
2. ✅ **HECHO** — Objetivo como **`/goal_pose`**: `goal_relay_node` lo convierte a la acción
   `NavigateToPose` de Nav2 (estado legible en `/nav2_relay/status`). Es lo que emitirá el MCP/LLM (Capa 3).
3. ✅ **HECHO** — Cerrar el **árbol TF** que espera Nav2: `map→odom` (emitido por `sim_map_grid`
   como identidad estática en banco; en real AMCL/SLAM), `odom→base_link` (odometría) y
   `base_link→laser` (URDF, `[0.070,0,0.028]`+180°). Se corrigió un árbol partido: `base_footprint`
   era padre de `base_link` chocando con `odom→base_link` → invertida la junta (base_link raíz).
   Árbol único `map→odom→base_link→{base_footprint,laser,imu,...}` verificado.
4. ✅ **HECHO — Nav2 FUNCIONA en el banco** y sustituye a `trajectory_nav` (que queda como modo
   RUTA aparte, andamio): BT Navigator + planner **Smac Hybrid-A\*** (car-like, `minimum_turning_radius`
   =0.93) + controlador **RPP** (D3 permitía TEB/RPP/MPPI; elegimos RPP) + costmaps (static `/map` +
   obstacle `/scan` + **range** ultrasonidos en el local + inflación) + **collision_monitor** (parada
   IR). Con **marcha atrás** (Reeds-Shepp; contradice el "forward-only" del plan viejo) y un BT sin
   recuperaciones-que-mueven (no se sale del mapa). La web da el **destino**; Nav2 planifica y conduce.
   Sin tocar `sim_sensors`/`sim_motion`/web: **el diseño drop-in se cumplió**.

> **Estado del banco (ago 2026): NAV2 FUNCIONANDO DE PUNTA A PUNTA.** Das un destino en la web (o
> `/goal_pose`) → Nav2 traza la ruta rodeando paredes y conduce. Incluye: **marcha atrás**,
> **obstáculos dinámicos** (canal `/sim_obstacles`: van al `/scan`, no al `/map`), **evitación** con
> los 3 ultrasonidos (`sensor_msgs/Range` → range_sensor_layer del costmap local) y **parada de
> emergencia IR** (`/ir_range` → `collision_monitor`, corta `/cmd_vel`). Contrato **`/nav_config`**
> (get/set JSON autodescrito) = **la interfaz de configuración para el LLM** (velocidad, marcha atrás,
> radio de giro, tolerancia, margen, orientación, centrado, suavidad, y **velocidad adaptativa** —
> frenado en curvas y cerca de obstáculos, verificado: mismo arco, frenado fuerte 0.31 vs suave 0.44 m/s);
> en caliente o con reinicio de Nav2 según el parámetro. Ver [Control de la navegación por el LLM](control-navegacion-llm.md).
>
> **Lo que queda para llevarlo al robot real** = la **Capa 1 (SLAM)**: cuando Cartographer publique un
> `/map` real, se enchufa en el costmap estático en lugar del simulado y **Nav2 no cambia** (drop-in).
> Opcional: `/scan` en frame `laser`, ultrasonidos también en el costmap global (hoy cuelgan el planner
> por TF timing).
>
> **Banco OPTIMIZADO (ago 2026):** la Pi4 iba justa (se congeló una vez); tras un plan de optimización
> medido nodo a nodo se recuperaron **>120 puntos de CPU y ~150 MB de RAM** — goal_relay 35→7 %,
> sim_map_grid 18→0.2 %, rosbridge 79→50 %, trajectory_nav 26→3 %, ray-cast vectorizado, `sim_motion`
> a 20 Hz (consumidores de odometría 88→60 %), binarios Nav2 sin wrappers. La Pi tiene ya holgura amplia.
> Ver [Plan de optimización del banco](optimizacion-banco.md).

## Decisiones de diseño

| ID | Decisión | Resolución |
|---|---|---|
| **D1** | Distro ROS2 | **Humble** (LTS hasta 2027, alineada con la memoria). Migración realizada. |
| **D2** | Odometría/localización | **Opción A**: pose por *scan-matching* de Cartographer. Plan B (fusión encoder+IMU+dirección → odometría modelo-bicicleta) **implementado y validado** en Capa 0 (~±1.5 % / ~2 cm a 30 Hz), disponible si no se cumple OE1 (<10 cm) y como base para el banco. |
| **D3** | Controlador local Nav2 → **RPP (elegido en el banco)** | En el banco se usa **Regulated Pure Pursuit** (RPP) con planner **Smac Hybrid-A\*** (car-like), no DWB diferencial. TEB queda como alternativa futura. Datos **medidos**: L=0.175 m, **R_min ≈ 0.93 m** (tan_max=0.188), velocidad mínima conducible **~0.3 m/s**. **Marcha atrás implementada** (Reeds-Shepp + `allow_reversing`; contradice el viejo "forward-only"). Config y "mandos" del LLM en **`/nav_config`**. |
| **D4** | Puente de actuación | `car_control_node` extendido (único dueño del bus I2C): `/cmd_vel` → servo dirección + ESC, con rampa anti-pico, watchdog y neutro garantizado. |

## Correspondencia fases ↔ capas ↔ objetivos

| Fase (memoria) | Capa | Objetivo | Métrica |
|---|---|---|---|
| Fase 1 · SLAM y mapa semántico | Capa 0 + Capa 1 | OE1 | Error localización < 10 cm |
| Fase 2 · Navegación con Nav2 | Capa 2 | OE2 | Éxito navegación > 90 % |
| Fase 3 · MCP Server | Capa 3 | OE3 | 4 tools operativas |
| Fase 4 · Integración con LLM | Capa 3 | OE4 | Interpretación NL > 85 % |
| Fase 5 · Pruebas y evaluación | Capa 4 | OE1-OE4 | + latencia mediana < 5 s |

> **Trabajo actual** (banco de simulación con plantas de piso + `trajectory_nav`) es
> **preparatoria de la Fase 2 / Capa 2**: valida el seguimiento de trayectoria y la evitación
> contra las **mismas interfaces** que consumirá Nav2 (ver sección *Banco de simulación*). La
> Capa 0 (odometría, actuación, TF) ya está validada y es la base sobre la que se monta.

## Riesgos estructurales

- **Capa 0 como cuello de botella**: TF, odometría y actuación Ackermann son el trabajo
  "invisible" del que depende todo lo demás (ver [Fundamentos ROS2](fundamentos.md)).
  *Estado:* odometría y actuación **validadas**; queda cerrar el árbol TF completo para Nav2.
- **Cómputo en la Raspberry Pi 4**: LIDAR + Cartographer + panel comparten CPU; el tuning
  de Cartographer (submaps y optimización contenidos) es parte del diseño.
- **Alimentación única** (batería → ESC + BUCK 5V compartido): las entradas de acelerador
  en escalón provocan caídas de tensión; se gestiona con rampas por software y protocolo
  operativo (el hardware no se modifica, por decisión de proyecto).
- **Fidelidad del banco**: el banco simulado sólo es útil si mantiene el **contrato de
  interfaces** con Nav2 (topics/tipos/frames/cinemática). Cualquier atajo que rompa ese
  contrato (p. ej. lógica de control que no salga por `/cmd_vel`, o sensores que no salgan por
  `/scan`) invalida la preparación. Ver checklist de convergencia arriba.
