# Plan de optimización del banco (simulación Nav2)

Plan para hacer el banco más **eficiente** (CPU/RAM en la Pi4), más **ordenado** (arranque
reproducible) y más **mantenible**, **sin romper lo que ya funciona**. Basado en la auditoría de
nodos y el perfilado de CPU medidos en la Pi el **20-ago-2026**.

> **Idea rectora:** el lenguaje **no** es la palanca. El trabajo pesado y siempre activo (Nav2)
> ya está en C++; nuestros nodos Python son *pegamento* (event-driven, ligeros) o *simulación*
> (desechables cuando llegue el robot real). Las ganancias están en **qué se streamea**, **arreglar
> bugs de CPU**, **vectorizar la simulación** y **componer/ordenar el arranque** — no en reescribir.

---

## 1. Diagnóstico (lo medido)

**CPU por nodo** (100 % = 1 core; la Pi4 tiene 4 cores = 400 %). Panel web conectado.

| Nodo | Lenguaje | reposo % | nav % | Lectura |
|---|---|---:|---:|---|
| rosbridge | Python (stock) | 82.7 | 87.5 | **#1** — coste de serializar sensores a la web |
| sim_sensors | Python (propio, sim) | 46.7 | 28.2 | Ray-cast del láser: pesado |
| goal_relay | Python (propio) | 0.0 | 36.8 | **Pico anómalo** en nav → sospecha de bug |
| sim_motion | Python (propio, sim) | 23.0 | 29.5 | Integrador a alta frecuencia |
| sim_map_grid | Python (propio, sim) | 18.0 | 17.8 | Alto para republicar a 1 Hz |
| Nav2 (bt+controller+planner+…) | C++ | ~60 | ~80 | Trabajo real de navegación (OK) |
| **TOTAL** | | **237** | **282** | La Pi va al **60–70 %**; poco margen |

**Hallazgos estructurales:**

1. **Arranque incoherente.** 5 de 6 nodos propios corren como *scripts sueltos* (`python3 …_node.py`),
   no por colcon; `sim_sensors` está en colcon pero se lanza suelto (el `install/` no refleja el
   código parcheado). No hay *launch file* único: todo es `bringupNAV2.sh` con `nohup`.
2. **Sobrecoste de wrappers.** Cada `ros2 run` deja vivo un proceso wrapper de ~23 MB además del
   nodo real. ≈ 7 wrappers ≈ **160 MB de RAM** en procesos que no hacen nada.
3. **`trajectory_nav` corre siempre**, también en modo Nav2 (ocioso pero suscrito a odometría y
   ultrasonidos).
4. **Posible remap suelto:** `controller_server` escucha `/odom`, pero `sim_motion` publica
   `/odometry/filtered` (funciona por TF, pero conviene fijar `odom_topic`).
5. **Pi4 justa** (ya se congeló una vez con todo el stack): rosbridge ~77 MB, rosapi ~66 MB, cada
   C++ Nav2 30–65 MB, cada Python nuestro 44–65 MB.

---

## 2. Principios del plan

- **Medir antes y después** con el mismo perfilador (`/proc`, `nav_cpu_profile.py`) y la RAM (`ps rss`).
- **No reescribir a C++** los nodos de simulación/pegamento (ROI negativo; se pierde la iteración
  rápida sin rebuild). Único "a C++" con sentido: cambiar el *componente* rosbridge por foxglove.
- **Trabajar en `main`**, un cambio cada vez, verificando que el banco sigue navegando de punta a punta.

---

## 3. Acciones priorizadas por ROI

### Tier 1 — Quick wins (alto valor, bajo esfuerzo)

**O1 · Arreglar el pico de CPU de `goal_relay` (37 % en nav).** ✅ **HECHO (20-ago)**
- *Problema (diagnosticado, no era lo que parecía):* el estado se publicaba a solo ~4 Hz, así que
  **no** era sobre-publicación. El pico venía de un **busy-spin del executor de rclpy**: mientras hay
  una acción `NavigateToPose` activa, una *guard condition* del *goal handle* queda siempre "lista"
  y `rclpy.spin()` gira a máxima velocidad **sin publicar nada** (medido: 35.6 % con 0 mensajes/s).
- *Solución:* bucle con frecuencia acotada (`spin_once` + `sleep 50 ms`) en vez de `rclpy.spin()`
  — atiende feedback/resultado/cancel con <20 ms de retardo pero elimina el giro en vacío. Además
  *dedupe* del estado + redondeo de distancia a 0.1 m (alivia también a rosbridge).
- *Resultado medido:* **35.6 % → 6.6 %** en nav (−81 %), idle 1.8 %. Navegación de punta a punta
  verificada (`DESTINO ALCANZADO`). Commit `2e545f46`.
- *Hallazgo lateral:* `restart_nav2` reescribe el yaml desde `self.vals`, así que un cambio de
  `marcha_atras`/`radio_giro_min` **persiste en disco** y cambia el comportamiento por defecto hasta
  revertirlo (nos dejó REEDS_SHEPP+reversa, que provocaba abortos "collision ahead"). → ojo en O6/O10.

**O2 · Recortar lo que la web streamea (ataca el 79 % de rosbridge).** ✅ **HECHO (20-ago)**
- *Problema (medido):* rosbridge es **un único proceso Python (GIL → tope ~1 core)** y estaba al
  **79 %** serializando a JSON todo lo que la web suscribe sin throttle: `/odometry/filtered` (49 Hz),
  `/scan` (~12 Hz, grande), `/global_costmap/costmap` (200×200 = **40 000 celdas**), `/map`, `/plan`.
- *Solución:* `throttle_rate` + `queue_length:1` en las suscripciones pesadas del cliente web:
  odometry 49→10 Hz, scan →5 Hz, costmap →1 Hz, map →0.5 Hz, plan →3 Hz. Los de texto (status,
  nav_config) sin throttle. Verificado con un cliente WS de prueba (odometry 49.8→9.7, scan 11.8→5.0).
- *Resultado medido:* **rosbridge 79 % → 50 %** (−37 %) con un panel. Commit `3f003f69`.
- *Gotcha:* solo aplica al **recargar** la página (F5); reconectar no basta (el JS viejo sigue en
  memoria). Y cada pestaña/cliente cuenta: 2 pestañas viejas sin throttle mantenían rosbridge alto.
- *Palanca extra (si se quiere <40 %):* subir el throttle de los dos `OccupancyGrid` grandes
  (`/global_costmap/costmap` a 2.5–3 s, `/map` a 5 s) — cambian despacio; o servir la vista costmap
  bajo demanda. No hay un culpable único (grids y scan/odom cuestan parecido), hay que apretar en varios.

**O3 · `sim_map_grid` que actúe solo al cambiar el mapa.** ✅ **HECHO (20-ago)**
- *Problema (medido):* 17.8 % de CPU. No era recalcular (el rasterizado ya era por evento), sino
  **mantener una suscripción a `/odometry/filtered` a 49 Hz** solo para cachear la pose. Confirmado:
  cambiarla por un `TransformListener` la dejó igual (17→17 %) — el coste es *consumir cualquier
  topic a 49 Hz*, no la deserialización concreta.
- *Solución:* **suscripción efímera** a odometría — se crea al llegar un `/sim_map`, captura una sola
  pose para anclar los segmentos, y se destruye (fuera de su callback, desde el timer). En reposo:
  cero topics de alta frecuencia consumidos.
- *Resultado medido:* **17.8 % → ~0.2 %** (idle). Mapa anclado y publicado OK (`/map`=180 celdas) y
  navegación de punta a punta verificada (`DESTINO ALCANZADO`). Commit pendiente.
- *Bonus:* limpiar el mapa (`/sim_map` vacío) ya no exige tener odometría.

### Tier 2 — Estructura (RAM + mantenibilidad)

**O4 · Quitar los wrappers `ros2 run` (−RAM).** ✅ **HECHO (20-ago)**
- *Problema (medido):* cada `ros2 run <pkg> <exe>` deja vivo un proceso wrapper Python de ~23 MB
  como padre del nodo real. **6 wrappers Nav2 = 138 MB** de RAM sin hacer nada.
- *Solución:* en `bringupNAV2.sh` y `restart_nav2.sh`, lanzar los **binarios directos**
  (`/opt/ros/humble/lib/nav2_*/…`) en vez de `ros2 run`. Mismos params/remaps/orden; el entorno
  (`ROS_LOCALHOST_ONLY=1`, RMW) se hereda del shell. Los nodos propios ya iban por python3 directo.
- *Resultado medido:* 0 wrappers, **RAM disponible +94 MB** (2812→2909 MB), Nav2 `active` y navegación
  de punta a punta OK (`DESTINO ALCANZADO`). Commit pendiente.
- *Paso extra futuro (más RAM, más riesgo):* **composición** (nodos Nav2 en un `ComposableNodeContainer`
  único) — ahorra memoria y coste de descubrimiento, pero es un cambio mayor. No hecho.

**O5 · Apagar `trajectory_nav` en modo Nav2.** ✅ **HECHO (20-ago)**
- *Problema (medido):* ocioso en modo Nav2 consumía **26 %** de CPU por escuchar `/odometry/filtered`
  a 49 Hz + `/ultrasound_data` (más un wrapper `ros2 run` de ~23 MB).
- *Solución (patrón efímero, como O3, sin romper la web):* odometría y ultrasonidos se **arman al
  recibir waypoints** y se **sueltan al terminar la ruta**; en modo Nav2 (sin ruta) queda ocioso sin
  consumir. Además pasado de `ros2 run` a **python3 directo** (usa `src`, quita el wrapper, −RAM).
- *Resultado medido:* **26 % → 3 %** ocioso. Modo RUTA verificado: ruta de 2 m seguida a completar
  (`state=DONE wp=2/2`, robot movió 1.81 m) y sensores soltados después. Commit pendiente.

**O6 · Decidir la política colcon (coherencia).**
- *Acción:* o bien **meter todos los nodos propios en colcon con `--symlink-install`** (coherente y
  editable sin rebuild — resuelve la razón por la que hoy van "sueltos"), o dejarlos sueltos **a
  propósito** y documentarlo. *Recomendado:* `colcon build --symlink-install` una vez → luego se edita
  el `src/` y `ros2 run` ya usa el código vivo.
- *Ganancia:* mantenibilidad; base para el `launch` de O4. *Esfuerzo:* bajo-medio. *Riesgo:* bajo.

### Tier 3 — CPU pesada (si necesitamos más margen)

**O7 · Vectorizar el ray-cast de `sim_sensors` con numpy.** ✅ **HECHO (20-ago)** — con matiz importante
- *Acción hecha:* el bucle rayo-a-rayo (120 rayos × N segmentos = ~45k llamadas Python/s) sustituido
  por una intersección **vectorizada** (todos los rayos contra todos los segmentos en una pasada numpy).
- *Correctitud verificada:* `/scan` idéntico físicamente (obstáculo a 1.0 m → rayo frontal = 1.00,
  pared trasera 2.50, ultrasonidos y IR correctos). *Bug encontrado y corregido:* `cast()` devolvía
  `np.float64` → `emergency_stop` daba `np.bool_` y el campo `bool` del mensaje lo rechazaba (crash);
  se fuerza `float()` nativo.
- *Resultado real:* **escala plano** (4 paredes 30.5 % → 19 paredes 31.5 %, +1 %) — con el bucle viejo
  se habría disparado. PERO **el 31 % de base NO baja**: está dominado por la suscripción a
  `/odometry/filtered` a **49 Hz** + el publicado (7 msgs × 12 Hz), no por el ray-cast.
- *Conclusión:* la vectorización es correcta y **evita que los planos con muebles disparen el CPU**,
  pero el número de cabecera de `sim_sensors` **solo baja con O8** (menos Hz de odometría). → **O8 es
  ahora la palanca clara** (toca a sim_sensors, sim_motion consumidores, etc. a la vez).

**O8 · Bajar la frecuencia de `sim_motion` (odom + TF).** ✅ **HECHO (20-ago)** — la palanca de fondo
- *Problema (medido):* `sim_motion` publicaba `/odometry/filtered` + TF a **60 Hz**; cada consumidor
  (sim_sensors, bt_navigator, controller, sim_motion mismo…) paga la deserializacion a 60 Hz. La
  **suma de consumidores = 88 %** de CPU.
- *Solución:* `sim_motion` a **20 Hz** (`-p rate_hz:=20.0` en el bringup; por encima del control a
  20 Hz, con margen). Sin tocar codigo, reversible.
- *Resultado medido (estado limpio):* **suma 88 % → 59.7 %** (**−28 pts**): sim_motion 25→11,
  sim_sensors 31.6→19, bt_navigator 14.8→11. Navegacion `DESTINO ALCANZADO`. Commit pendiente.
- *Lección operativa (→ O10/robustez):* reiniciar en caliente un nodo que publica **TF**
  (`sim_motion` = odom→base_link, `sim_map_grid` = map→odom) corrompe la cache TF/costmap y provoca
  "message filter dropping" + "collision ahead". **Tras tocar un nodo de TF, hacer bringup completo**,
  no reinicio suelto.

**O9 · (Opcional, mayor) rosbridge → `foxglove_bridge` (C++).**
- *El único cambio "a C++" con ROI real.* Es un **swap de componente**, no reescribir código nuestro.
- *Riesgo:* alto — cambia el protocolo; habría que adaptar el cliente web (hoy usa la API de rosbridge).
  Dejar para el final y solo si O2 no basta.

### Tier 4 — Correcciones de fondo

**O10 · Fijar el `odom_topic` del `controller_server`** a `/odometry/filtered` (o remapear `/odom`).
Correctness, no CPU.

**O11 · Gestión de carga en la Pi4:** `nice`/`cpuset` para acotar la simulación, o mover la web
(rosbridge + http.server) a otra máquina para liberar la Pi.

---

## 4. Orden recomendado y objetivo

**Secuencia:** ~~O1~~ ✅ → ~~O3~~ ✅ → ~~O2~~ ✅ → ~~O5~~ ✅ → ~~O4~~ ✅ → ~~O7~~ ✅ → ~~O8~~ ✅ → (quedan O6/O9/O10/O11, menores).

> **Progreso CPU (medido):** goal_relay 35.6→6.6 (O1) · sim_map_grid 17.8→0.2 (O3) · rosbridge
> 79→50 (O2) · trajectory_nav 26→3 (O5) · O8 bajó la suma de consumidores de odometría **88→60**
> (sim_motion 25→11, sim_sensors 31.6→19, bt_navigator 15→11). En total **>120 puntos de CPU**.
> **Progreso RAM:** O4 quitó 6 wrappers `ros2 run` = **138 MB** (+94 MB disponibles medidos) + O5 otro.
> **La Pi ha pasado de ir al ~60-70 % (y congelarse) a holgura amplia.** O7 además evita que los
> planos con muebles disparen el CPU (ray-cast vectorizado, escala plano).
> Insight recurrente: consumir topics de alta frecuencia (49 Hz odom / 20 Hz control) en Python es
> caro; **O8 (bajar la frecuencia de `sim_motion`) aliviaría a varios nodos a la vez** → sube prioridad.

**Objetivo cuantitativo:** bajar de **282 % (nav)** a **< 200 %** de CPU y **−150 MB** de RAM,
manteniendo la navegación de punta a punta. Cada paso se valida con el perfilador antes de seguir.

## 5. Qué NO vamos a hacer

- **No** portar `sim_motion`, `sim_sensors`, `sim_map_grid`, `goal_relay`, `nav_config` ni
  `trajectory_nav` a C++: son desechables (simulación) o ya ligeros (pegamento), y perderíamos la
  edición sin rebuild. El reparto Python/C++ actual es el correcto.

---

*Medido y redactado el 20-ago-2026. Perfilador: `nav_cpu_profile.py` (lee `/proc/<pid>/stat`).
Ver también: [Mapa de nodos](nodos-ros2.html) y [Control por el LLM](control-navegacion-llm.md).*
