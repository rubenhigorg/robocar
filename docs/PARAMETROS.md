# Registro de parametros configurables — Robocar

Documento vivo: **fuente unica de verdad** de los parametros ajustables del robot, a quien
pertenecen, que hacen y su valor mas adecuado. Mantener en sincronia con los ficheros reales:
- `src/robocar_pkg/config/nav2_real.yaml` (Nav2: planner, controller, costmaps, amcl, collision_monitor, bt)
- `src/robocar_pkg/robocar_pkg/car_control_node.py` (lazo de velocidad / puente Ackermann)

**Ultima verificacion:** 2026-08-24 (mapa casa4, map_server + AMCL, lazo PI cerrado).
Plan de pruebas asociado: ver artifact "Plan de pruebas navegacion casa4" (fases P0..P10).

## Como mantener este registro
1. Cuando cambies un valor y lo **valides** en pruebas: actualiza *Actual*, *Adecuado* y *Estado* aqui, y commitea junto al fichero real.
2. Un cambio por prueba; anota el motivo en *Notas*.
3. Este doc NO se lee solo: hay que aplicar los cambios en el YAML / .py de verdad.

## Leyenda
- **Aplicar:** `LIVE` = se cambia en caliente con `ros2 param set` (sin reiniciar) · `REINICIO` = editar YAML/py + rearrancar el nav.
- **Estado del valor:** ✅ tuneado/ok · 🔧 pendiente de afinar en pruebas (P#) · 💡 posible mejora sugerida · 🔒 no tocar (regla dura / calibracion HW / limite fisico).

---

## 1 · car_control_node  (`/car_control_node`, python3 directo)
Puente `/cmd_vel` (Twist) → servos ESC/direccion + **lazo de velocidad PI cerrado** con el encoder. Todos los parametros se leen en cada comando → **todos LIVE**. Ajustar SOBRE SUELO real (con ruedas al aire el lazo no tiene feedback valido).

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `closed_loop` | activa el PI (false = solo feed-forward) | true | true | LIVE | ✅ false solo para comparar (P9.2) |
| `vel_kp` | correccion proporcional al error de velocidad | 18.0 | ~18 | LIVE | 🔧 P9.1: ↑ responde antes; si vibra ↓ |
| `vel_ki` | elimina el error permanente de velocidad | 6.0 | ~6 | LIVE | 🔧 P9.1: ↑ si se queda corto; ↓ si sobrepasa |
| `vel_i_max` | tope de la parte integral (anti-windup), grados | 16.0 | ~16 | LIVE | 🔧 P9.1 |
| `stall_speed_eps` | umbral de "parado" (m/s) para anti-patinaje | 0.03 | 0.03 | LIVE | ✅ ↑ si el ruido de odom confunde |
| `stall_timeout` | s dando gas sin moverse → pulso neutro | 1.2 | ~1.2 | LIVE | 🔧 P2.3: ↑ mas margen a arrancar; ↓ corta antes el patinaje |
| `max_throttle_step` | rampa: grados de gas por comando (anti-pico) | 0.5 | 0.5 | LIVE | 🔧 ↑ arranque mas agil; ↓ mas suave |
| `throttle_stop` | NEUTRO del ESC (para y ARMA el ESC) | 93.6 | 93.6 | LIVE | 🔒 calibracion ESC — no tocar sin recalibrar armado |
| `throttle_start` | umbral donde empieza a moverse (adelante) | 90.0 | 90.0 | LIVE | ✅ feed-forward adelante |
| `throttle_full` | gas a `max_linear` (adelante, conservador) | 78.0 | 78.0 | LIVE | ✅ |
| `throttle_rev_start` | umbral de reversa (angulo sobre neutro) | 97.0 | ~97 | LIVE | 🔧 P5: calibrar arranque de reversa |
| `throttle_rev_full` | reversa a `max_linear_rev` | 108.0 | ~108 | LIVE | 🔧 P5 |
| `max_linear` | m/s que mapea a `throttle_full` | 0.7 | 0.7 | LIVE | ✅ escala del feed-forward adelante |
| `max_linear_rev` | m/s que mapea a `throttle_rev_full` | 0.5 | 0.5 | LIVE | ✅ reversa mas lenta |
| `max_angular` | rad/s que mapea a giro pleno de direccion | 0.4 | 0.4 | LIVE | ✅ |
| `steer_center` | centro del servo de direccion | 105.0 | 105.0 | LIVE | 🔒 calibracion mecanica del volante |
| `steer_span` | recorrido max de direccion (grados) | 65.0 | 65.0 | LIVE | ✅ tope de giro |
| `cmd_vel_timeout` | s sin /cmd_vel → throttle a neutro (deadman) | 0.5 | 0.5 | LIVE | ✅ seguridad |
| `autonomous_start` | arranca en modo autonomo (Nav2 conduce) | true | true | REINICIO | ✅ lo pone bringupNAVREAL |
| `THROTTLE_HARD_FLOOR` | tope duro de gas adelante (50%) | 59.4 | 59.4 | (const) | 🔒 REGLA DURA (Ruben) — no superar |
| `THROTTLE_HARD_CEIL` | tope duro de gas reversa (50%) | 124.0 | 124.0 | (const) | 🔒 REGLA DURA — no superar |

---

## 2 · Planner — Smac Hybrid-A*  (`/planner_server` → `GridBased`)
Traza la RUTA global respetando el radio de giro del coche (Ackermann).

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `motion_model_for_search` | modelo cinematico de busqueda | DUBIN | REEDS_SHEPP | REINICIO | 🔧 DUBIN=solo adelante (ahora). REEDS_SHEPP cuando la reversa este validada (P5) |
| `minimum_turning_radius` | radio de giro minimo (m) | 0.930 | 0.930 | REINICIO | 🔒 limite FISICO del coche — no bajar |
| `reverse_penalty` | coste de ir hacia atras | 2.0 | 2.0 | LIVE | ✅ usa reversa solo si hace falta |
| `change_penalty` | coste de cambiar de sentido | 0.40 | ~0.40 | LIVE | 🔧 P5.3: ↓ si no completa 3 puntos; ↑ si zigzaguea |
| `non_straight_penalty` | coste de girar vs recto | 1.3 | 1.3 | LIVE | ✅ ↑ rutas mas rectas |
| `cost_penalty` | evitar acercarse a obstaculos | 2.0 | 2.0 | LIVE | ✅ ↑ mas lejos de paredes |
| `allow_unknown` | cruzar celdas desconocidas | false | false | LIVE | ✅ el /map guardado no tiene gris |
| `tolerance` | distancia aceptable al goal si no llega exacto (m) | 0.25 | 0.25 | LIVE | ✅ |
| `analytic_expansion_ratio` | enganche analitico al goal | 3.5 | 3.5 | LIVE | ✅ (max_length 3.0) |
| `max_planning_time` | tiempo max de calculo (s) | 5.0 | ~3.0 | LIVE | 💡 5 s es mucho; ~3 responde antes si no hay ruta |
| `max_iterations` | tope de iteraciones de busqueda | 1000000 | 1000000 | LIVE | ✅ |
| `angle_quantization_bins` | resolucion angular de busqueda | 72 | 72 | REINICIO | ✅ ↑ giros mas finos/lento |
| `smooth_path` | suaviza la ruta resultante | true | true | REINICIO | ✅ |

---

## 3 · Controller — Regulated Pure Pursuit  (`/controller_server` → `FollowPath`)
CONDUCE: sigue la ruta soltando `/cmd_vel_raw`. `controller_frequency: 20 Hz`, `failure_tolerance: 0.3`.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `desired_linear_vel` | velocidad crucero (m/s) | 0.120 | 🔧 P3 | LIVE | 🔧 subir escalonado hasta el techo fiable en interior |
| `lookahead_dist` | distancia del punto de persecucion (m) | 0.60 | 0.60 | LIVE | ✅ ↑ suave/corta curvas; ↓ agresivo |
| `min_lookahead_dist` / `max_lookahead_dist` | limites del lookahead escalado | 0.3 / 0.9 | 0.3 / 0.9 | LIVE | ✅ |
| `use_velocity_scaled_lookahead_dist` | lookahead crece con la velocidad | true | true | LIVE | ✅ |
| `use_regulated_linear_velocity_scaling` | frena en curvas cerradas | true | true | LIVE | ✅ |
| `regulated_linear_scaling_min_radius` | radio bajo el que empieza a frenar (m) | 2.00 | ~1.0 | LIVE | 💡 2.0 > todas las curvas → frena en CASI TODAS. Bajar a ~1.0 para mantener velocidad en curvas amplias |
| `regulated_linear_scaling_min_speed` | velocidad minima al frenar en curva (m/s) | 0.120 | 0.120 | LIVE | ✅ |
| `use_cost_regulated_linear_velocity_scaling` | frenar por coste cerca de obstaculos | false | 💡 valorar true | LIVE | 💡 OFF ahora; true ralentizaria junto a paredes (mas seguro en pasillos) |
| `inflation_cost_scaling_factor` | debe casar con `cost_scaling_factor` del local | 3.00 | 3.00 | LIVE | ✅ |
| `use_rotate_to_heading` | girar en el sitio | false | false | LIVE | 🔒 Ackermann NO puede — siempre false |
| `allow_reversing` | ejecutar tramos de reversa | false | true | LIVE | 🔧 true para giros de 3 puntos (P5), junto con REEDS_SHEPP |
| `use_collision_detection` | mira el costmap local (laser vivo) para frenar | true | true | LIVE | ✅ evita chocar aunque AMCL este algo mal |
| `max_allowed_time_to_collision_up_to_carrot` | horizonte de frenada por colision (s) | 1.0 | 1.0 | LIVE | ✅ ↑ frena antes |
| `min_approach_linear_velocity` | velocidad minima al acercarse al goal (m/s) | 0.05 | 0.05 | LIVE | ✅ (approach_velocity_scaling_dist 0.6) |
| `max_angular_accel` | aceleracion angular max (rad/s2) | 3.2 | 3.2 | LIVE | ✅ |
| `transform_tolerance` | tolerancia temporal de TF (s) | 0.2 | 0.2 | LIVE | ✅ |

### 3b · Progress + Goal checker (`/controller_server`)
| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `progress_checker.required_movement_radius` | mov minimo para considerar "progreso" (m) | 0.10 | 0.10 | LIVE | ✅ |
| `progress_checker.movement_time_allowance` | tiempo de gracia sin progreso antes de abortar (s) | 30.0 | 30.0 | LIVE | ✅ ↓ si quieres que se rinda antes |
| `general_goal_checker.xy_goal_tolerance` | radio de "llegada" al destino (m) | 0.300 | 0.300 | LIVE | ✅ |
| `general_goal_checker.yaw_goal_tolerance` | tolerancia de orientacion final (rad) | 3.15 | 3.15 | LIVE | ✅ 3.15 = IGNORA orientacion final (Ackermann no la borda) |

---

## 4 · Global costmap  (`/global_costmap`)
El "mundo" para planificar: mapa estatico (/map) + obstaculos del laser + inflado. `update/publish 1/1 Hz`, `resolution 0.05`.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `robot_radius` | radio duro del coche | 0.12 | 🔧 0.10-0.12 | LIVE | 🔧 fisico ~0.09-0.11; bajar si roza puertas (P4.5), subir si quieres mas margen |
| `inflation_layer.inflation_radius` | halo alrededor de obstaculos (m) | 0.15 | 🔧 0.12-0.18 | LIVE | 🔧 ↑ se aleja de paredes (puede tapar puertas); ↓ roza mas |
| `inflation_layer.cost_scaling_factor` | pendiente del inflado | 3.00 | 3.00 | LIVE | ✅ debe casar con RPP inflation_cost_scaling_factor |
| `static_layer.lethal_cost_threshold` | umbral para tratar celda del mapa como pared | 55 | 55 | REINICIO | ✅ (mapa cartografiado: paredes a prob 50-98) |
| `static_layer.map_subscribe_transient_local` | el /map es latched | true | true | REINICIO | 🔒 dejar true |
| `obstacle_layer.obstacle_max_range` | alcance para marcar obstaculo del /scan (m) | 4.0 | 4.0 | LIVE | ✅ |
| `obstacle_layer.raytrace_max_range` | alcance para borrar libre (m) | 4.5 | 4.5 | LIVE | ✅ debe ≥ obstacle_max_range |
| `obstacle_layer.max_obstacle_height` | altura max que cuenta como obstaculo (m) | 2.0 | 2.0 | LIVE | ✅ |

---

## 5 · Local costmap  (`/local_costmap`)
Ventana movil (4x4 m) para el controller: obstaculos cercanos en vivo. `update/publish 5/2 Hz`. NO lleva mapa estatico.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `robot_radius` | radio del coche | 0.12 | = global | LIVE | 🔧 mantener igual que el global |
| `inflation_layer.inflation_radius` | halo local (m) | 0.15 | = global | LIVE | 🔧 mantener igual que el global |
| `width` / `height` | tamano de la ventana movil (m) | 4 / 4 | 4 / 4 | REINICIO | ✅ ↑ ve mas alrededor/mas CPU |
| `obstacle_layer` (scan) | marca obstaculos del /scan | 4.0/4.5 | = global | LIVE | ✅ mismos rangos que el global |
| `range_layer` | 3 ultrasonidos para evitacion local | /us_center,left,right | on | REINICIO | ✅ input_sensor_type ALL, clear_on_max_reading true |

---

## 6 · AMCL — localizacion  (`/amcl`)
Filtro de particulas: infiere la pose (map→odom) casando /scan con /map. `robot_model_type: Differential`, `laser_model: likelihood_field`.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `update_min_d` | mov lineal para actualizar (m) | 0.15 | 💡 0.05-0.10 | REINICIO | 💡 bajar → corrige la pose antes al moverse (P1.2), a costa de CPU |
| `update_min_a` | mov angular para actualizar (rad) | 0.20 | 💡 0.10 | REINICIO | 💡 bajar → endereza el giro antes |
| `min_particles` / `max_particles` | tamano de la nube | 500 / 3000 | 500 / 3000 | REINICIO | ✅ ↑ mas robusto/lento |
| `alpha1..alpha5` | ruido esperado de la odometria | 0.2 (todos) | 🔧 afinar | REINICIO | 🔧 ajustar segun cuanto derive la odom real; ↑ confia menos en el encoder |
| `recovery_alpha_slow` | inyeccion lenta al perderse | 0.001 | 0.001 | REINICIO | 🔒 NUNCA 0 (mata AMCL — comprobado) |
| `recovery_alpha_fast` | inyeccion rapida al perderse | 0.10 | 0.10 | REINICIO | ✅ ↑ recupera antes/mas inestable |
| `laser_max_range` | alcance del laser usado (m) | 4.0 | 4.0 | REINICIO | ✅ (RPLIDAR C1) |
| `laser_min_range` | alcance minimo (m) | 0.1 | 0.1 | REINICIO | ✅ |
| `max_beams` | nº de rayos usados por scan | 60 | 60 | REINICIO | ✅ ↑ mas info/CPU |
| `z_hit` / `z_rand` / `sigma_hit` | modelo de medida del laser | 0.5 / 0.5 / 0.2 | ✅ | REINICIO | ✅ likelihood_max_dist 0.3 |
| `set_initial_pose` | arranca con pose fijada | true | true | REINICIO | ✅ como en simulacion |
| `initial_pose {x,y,yaw}` | pose HOME de arranque | 0.13, 0.56, 1.676 | por mapa | REINICIO | 🔧 ajustar al punto fisico de partida de cada mapa |
| `first_map_only` | no re-init al re-publicar /map | true | true | REINICIO | 🔒 dejar true (evita re-localizar cada seg) |
| `transform_tolerance` | tolerancia de TF (s) | 1.0 | 1.0 | REINICIO | ✅ |

---

## 7 · Collision monitor  (`/collision_monitor`)
Reflejo de seguridad entre Nav2 y el coche: `cmd_vel_raw` → (si el IR ve algo en la zona) → corta → `cmd_vel`.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `StopZone.points` | caja de parada frontal (m) | x:0.03→0.38, y:±0.16 | ~ | REINICIO | ✅ 0.38 fondo x 0.32 ancho; ↑ frena antes |
| `StopZone.action_type` | accion al invadir la zona | stop | stop | REINICIO | ✅ parada de emergencia |
| `observation_sources` | sensor de parada | ["ir"] (/ir_range) | ir | REINICIO | 🔒 el LIDAR daba falsos positivos → se dejo el IR |
| `source_timeout` | caducidad del dato del sensor (s) | 1.0 | 1.0 | REINICIO | ✅ |
| `stop_pub_timeout` | duracion de la parada publicada (s) | 2.0 | 2.0 | REINICIO | ✅ |
| `base_shift_correction` | corrige el poligono con el movimiento | true | true | REINICIO | ✅ |

---

## 8 · BT navigator  (`/bt_navigator`)
El "director de orquesta": recibe el destino y coordina planner + controller.

| Parametro | Que hace | Actual | Adecuado | Aplicar | Estado · Notas |
|---|---|---|---|---|---|
| `default_nav_to_pose_bt_xml` | arbol de comportamiento por defecto | nav2_bt_no_move.xml | = | REINICIO | ✅ arbol SIN recuperaciones que muevan (no spin/backup) → no se sale del mapa |
| `bt_loop_duration` | periodo del tick del BT (ms) | 10 | 10 | REINICIO | ✅ |
| `default_server_timeout` | timeout de los servidores (s) | 20 | 20 | REINICIO | ✅ |

> Nota: el `behavior_server` tiene definidos spin/backup/drive_on_heading/wait, pero el BT actual NO los invoca (a proposito). Si algun dia se quiere recuperacion por retroceso, cambiar el XML del BT.

---

## Resumen de lo pendiente de afinar (🔧 / 💡)
| Parametro | Dueno | Ahora | Objetivo | Donde se decide |
|---|---|---|---|---|
| `desired_linear_vel` | controller | 0.120 | techo fiable interior | P3 (barrido) |
| `vel_kp` / `vel_ki` / `vel_i_max` | car_control | 18 / 6 / 16 | seguimiento limpio | P9.1 |
| `stall_timeout` | car_control | 1.2 | no patinar sin cortar arranque | P2.3 |
| `motion_model_for_search` + `allow_reversing` | planner + controller | DUBIN / false | REEDS_SHEPP / true | tras validar P2-P4 → P5 |
| `throttle_rev_start/full` | car_control | 97 / 108 | reversa fiable | P5 |
| `change_penalty` | planner | 0.40 | completar 3 puntos | P5.3 |
| `regulated_linear_scaling_min_radius` | controller | 2.0 | ~1.0 (no frenar en curvas amplias) | P4 |
| `use_cost_regulated_linear_velocity_scaling` | controller | false | valorar true | P6 |
| `robot_radius` / `inflation_radius` | costmaps | 0.12 / 0.15 | pasar puertas sin rozar | P4.5 |
| `update_min_d` / `update_min_a` | amcl | 0.15 / 0.20 | corregir pose antes | P1.2 |
| `alpha1..5` | amcl | 0.2 | segun deriva real de odom | P1.4 |
