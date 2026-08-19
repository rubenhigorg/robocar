# Control de la navegación por el LLM (Capa 3)

Análisis de **todo lo que un LLM podría controlar** en la navegación del robocar, agrupado en
dos familias: **cómo se mueve** (velocidad y estilo) y **dónde/por dónde va** (la ruta y sus
restricciones). Es el catálogo de "mandos" que expondremos al modelo en la Capa 3, sobre Nav2.

**Estado (leyenda):** ✅ ya implementado · ⚙️ activo o exponible (falta sacarlo al contrato) ·
🔨 requiere montar algo · 🔬 avanzado.

El contrato base ya existe: **`/nav_config`** (get autodescrito) + **`/nav_config/set`**, con 8
parámetros hoy: velocidad, marcha_atras, radio_giro_min, tolerancia_objetivo, margen_seguridad,
orientacion_final, distancia_paredes (tendencia al centro), suavidad. Ampliarlo es "más de lo mismo".

---

## A) Velocidad — que NO sea constante

La idea: rápido en rectas, lento en curvas, prudente cerca de obstáculos, despacio en ciertas zonas.

| Palanca | Qué hace | Nav2 | Estado | Control LLM |
|---|---|---|---|---|
| **Velocidad base** | crucero en recto | `FollowPath.desired_linear_vel` | ✅ | "ve más rápido/lento" |
| **Frenar en curvas** | baja según lo cerrada que sea la curva (regulated scaling de RPP) | `regulated_linear_scaling_min_radius` / `_min_speed` | ⚙️ **ya activo**; falta exponer intensidad | "frena más en las curvas" |
| **Frenar cerca de obstáculos** | reduce al aproximarse a algo | RPP cost-regulated + zona **slowdown** del collision_monitor | 🔨 | "sé prudente cerca de cosas" |
| **Aceleración / suavidad** | cómo de brusco acelera/frena | `nav2_velocity_smoother` | 🔨 (añadir nodo) | "arranca/para suave" |
| **Frenar al llegar** | reduce al aproximarse al destino | `approach_velocity_scaling_dist` | ⚙️ ya | — |
| **Suavidad de trazado** | ceñido vs cómodo | `lookahead_dist` | ✅ (`suavidad`) | "conduce más suave" |
| **Límite de velocidad por ZONA / global** | "en la cocina, despacio" | `SpeedFilter` + topic `/speed_limit` | 🔨 mecanismo nuevo | **muy potente**: "en el pasillo al 30%" |

**Nota clave:** "más rápido en rectas, lento en curvas" **ya ocurre** — RPP regula la velocidad con
la curvatura del camino. Lo que falta es dejar que el LLM ajuste *cuánto* frena y ponga **límites por zona**.

---

## B) Condicionar la ruta — dónde y por dónde

| Palanca | Qué hace | Nav2 | Estado | Control LLM |
|---|---|---|---|---|
| **Pasar por puntos intermedios** | lista ordenada de poses | `NavigateThroughPoses` (navigator ya configurado) | 🔨 | "ve a la cocina **pasando por** el salón" |
| **Zonas prohibidas (keepout)** | máscara de "no entres aquí" | `KeepoutFilter` (costmap filter + mask) | 🔨 | "**no entres** al dormitorio" |
| **Zonas de velocidad** | máscara de límite por área | `SpeedFilter` (= arriba) | 🔨 | "en el baño ve despacio" |
| **Pegado a pared vs centro** | ceñirse a paredes o buscar el centro | `cost_penalty` (Smac) + inflation `cost_scaling_factor` | ⚙️ **ya parcial** (`distancia_paredes`) | "ve **pegado a la pared** / por el centro" |
| **Orientación de llegada** | llegar mirando a una dirección | `xy/yaw_goal_tolerance` | ✅ (`orientacion_final`) | "aparca mirando a la puerta" |
| **Estilo de ruta** | suave/directa, evitar reversa | Smac `reverse_penalty` / `change_penalty` / `non_straight_penalty` | ⚙️ exponible | "ruta más directa", "evita marcha atrás" |
| **Carriles / rutas preferidas** | seguir un grafo de rutas definido | `nav2_route` (**ya instalado**) | 🔬 avanzado | "ve **por el pasillo central**" |
| **Modo de comportamiento** | cauto vs rápido, con/sin recuperación | árbol de comportamiento (BT) | ⚙️ exponible (elegir BT) | "sé **cauteloso** aquí" |

---

## Arquitectura de control para el LLM

Conviene distinguir **dos vías**, porque son mecanismos distintos:

1. **Parámetros de comportamiento** ("cómo se mueve") → **el contrato `/nav_config`** (el que ya existe).
   El LLM lee las opciones (autodescritas) y escribe valores. Aquí entran: velocidad, frenos, aceleración,
   estilo de ruta, pegado/centro, orientación… Ampliarlo es barato.

2. **Especificación de tarea** ("a dónde y con qué condiciones") → **mensajes de objetivo más ricos**:
   - Un punto: `/goal_pose` (ya).
   - Varios puntos en orden: `NavigateThroughPoses` → "pasa por X".
   - **Restricciones espaciales** = "máscaras" que el LLM define: **keepout** (prohibido) y **speed** (lento).
     Es como los obstáculos que ya se pintan en la web, pero con semántica de zona.

```
LLM ──▶ /nav_config/set              (comportamiento: velocidad, frenos, estilo…)
LLM ──▶ /goal_pose | ThroughPoses    (a dónde, por dónde)
LLM ──▶ máscaras keepout / speed     (zonas prohibidas / lentas)
```

Cuando se monte el **MCP** (Capa 3), cada bloque se envuelve en una *tool*:
`set_nav_config(...)`, `navigate_to(place)`, `navigate_through(places)`, `set_zone(area, keepout|slow)`.
La resolución semántica ("la cocina" → coordenada) es la pieza de la Capa 2 (SQLite lugar→pose).

---

## Hoja de ruta propuesta (de más valor / menos esfuerzo a más avanzado)

1. **Ampliar `/nav_config`** con velocidad adaptativa: `frenar_en_curvas`, `frenar_obstaculos`
   (slowdown del collision_monitor), `aceleracion` (velocity_smoother), y `estilo_ruta`
   (penalties de Smac). Todo por el mismo patrón (en caliente / reinicio). **Empezar aquí.**
2. **NavigateThroughPoses** ("pasa por…") + exponerlo en la web y como *tool*.
3. **Zonas keepout + speed** (máscaras): "no entres aquí" / "aquí despacio". Muy visual en la web
   (como los obstáculos) y muy potente para el LLM.
4. **Estilo pegado/centro fino** y **carriles** (`nav2_route`) — avanzado, para el final.

## Avisos

- Muchas palancas de **Smac (planner)** NO son seguras en caliente (cuelgan el planner) → van por
  **reescribir yaml + reinicio** (ya resuelto en `nav_config` para marcha_atras/radio_giro).
- La **Pi4 va justa** con todo el stack; añadir nodos (velocity_smoother, filtros) hay que vigilarlo.
- Ver también: [Roadmap](roadmap.md) (Capa 2/3) y [De cero: nodos, topics, TF y Nav2](de-cero-nodos-tf-nav2.md).
