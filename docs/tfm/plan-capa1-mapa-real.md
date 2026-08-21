# Plan · Capa 1: del banco a la realidad (mapa real + migración)

Objetivo en tres saltos: **(A)** cartografiar el piso real con el mando (Cartographer/SLAM),
**(B)** meter ese mapa real en el simulador y repetir las pruebas del banco sobre él, y **(C)** migrar
la navegación al robot real y adaptar la web para observarla. Todo reutiliza lo que ya existe.

## Punto de partida (lo que YA está montado)

| Pieza | Estado | Dónde |
|---|---|---|
| **RPLIDAR** (láser 2D real) | driver instalado | `rplidar_ros` |
| **Cartographer 2D** | launch + config listos | `robocar_slam/launch/slam.launch.py`, `config/robocar_2d.lua` |
| **EKF** (odometría fusionada encoders+IMU) | listo | `robocar_pkg/launch/ekf.launch.py` → `/odometry/filtered` |
| **Odometría láser (RF2O)** | disponible (fuente extra) | `rf2o_laser_odometry` |
| **TF / URDF** | listo | `robocar_description/launch/description.launch.py` |
| **Nodos HW reales** | existen | `encoder_node`, `steer_yaw_node`, `car_control_node`, `accelerometer_node` |
| **Teleop** | PS3 (BT) + mando web | `mando.html → /cmd_vel` (rosbridge) |
| **Nav2** | config del banco (a adaptar a real) | `config/nav2_bench.yaml` |
| **Panel web** | observa topics estándar (`/scan`,`/map`,`/amcl_pose`,`/plan`,`/odometry/filtered`) | `trayectorias.html` |

> Conclusión: **no se construye desde cero**; se orquesta lo existente y se cubren 3 huecos
> (bringup real, formato de mapa raster↔segmentos, y un modo "observación real" en la web).

---

## Fase A — Cartografía real del piso con el mando

**Meta:** conducir el robot a mano por el piso mientras Cartographer construye el mapa, y guardarlo.

### A1 · Poner el robot en el estado correcto (bringup real)
Cadena mínima, en orden (cada uno depende del anterior):
1. `description.launch.py` — TF del robot (base_link, laser_frame, ruedas…).
2. Nodos HW: `encoder_node`, `steer_yaw_node`, `car_control_node`, `accelerometer_node`/IMU.
3. `ekf.launch.py` — fusiona encoders+IMU → `/odometry/filtered` (+ TF `odom→base_link`).
4. **RPLIDAR** — `ros2 launch rplidar_ros ...` → `/scan` (verificar frame y montaje).
5. `robocar_slam/slam.launch.py` — Cartographer (usa `/scan` + `/odometry/filtered`) → `/map`.

- **Hueco a cubrir:** hoy solo existe `bringupNAV2.sh` (banco). Crear **`bringupREAL.sh`**
  (o `bringup_slam.sh`) que arranque 1–5 con `ROS_LOCALHOST_ONLY=1`, análogo al del banco.
- **Verificaciones antes de mover:** `/scan` a >5 Hz y sin huecos; TF `map→odom→base_link→laser`
  completa (`ros2 run tf2_tools view_frames`); `/odometry/filtered` avanza al empujar el coche.

### El origen (0,0) del mapa — lo fija el robot al arrancar
En SLAM **no se configura (0,0) a mano**: Cartographer ancla el frame `map` en la **pose (posición +
rumbo) donde está el robot al lanzar `bringupSLAM.sh`**. Ese instante pasa a ser el **(0, 0, 0)**; el eje
**+X** del mapa es hacia donde **mira** el robot al arrancar. (El EKF también arranca en 0 ahí; no hay
pose inicial que dar — eso es de **AMCL**, no de SLAM.)

**Elige el «punto base» a propósito ANTES de lanzar:**
- **Sitio fijo y repetible** (una esquina, la puerta de entrada, un dock) y **márcalo físicamente**
  (cinta en el suelo) — lo reusarás en la Fase C.
- **Rumbo alineado con la casa** (arranca mirando a lo largo de un pasillo/pared) → el mapa sale
  «recto», con los ejes paralelos a las paredes, en vez de torcido.
- **Robot quieto los primeros ~2 s**: el `accelerometer_node` calibra el bias del giróscopo asumiendo
  que no se mueve.

**Por qué importa aguas abajo:** en la **Fase B** el simulador también arranca en el origen (encaja
directo); en la **Fase C**, si **siempre colocas el robot en ese mismo punto base marcado**, la pose
inicial de AMCL es trivial (o le das la `📌 pista` ahí). Por eso el (0,0) debe ser un sitio
**reconocible y repetible**.

### A2 · Teleoperar para cartografiar
- **Mando:** PS3 por BT (recipe ya documentada) **o** el mando web (`:8080/mando.html`).
- **Buenas prácticas SLAM (Ackermann):** velocidad baja y constante; **bucles cerrados** (volver a
  sitios ya vistos ayuda al *loop closure*); giros suaves (el coche no gira en el sitio); evitar
  pasillos largos sin rasgos; recorrer pegado a paredes y luego el centro.
- **Vigilar en vivo** (RViz o el panel): que `/map` crezca coherente y no "resbale" (si patina la
  odometría, el mapa se dobla → bajar velocidad, revisar EKF).

### A3 · Guardar el mapa
- Serializar Cartographer: `pbstream` (estado del SLAM) **y** exportar occupancy grid:
  `ros2 run nav2_map_server map_saver_cli -f ~/robocar/maps/piso_real` → `piso_real.pgm` + `.yaml`.
- Guardar en `robocar_slam/maps/` (o `~/robocar/maps/`), versionado en git.

**Decisiones Fase A:** (a) ¿mando PS3 o web para cartografiar? (b) ¿una sola pasada o varias sesiones
fusionadas? (c) resolución del mapa (0.05 por defecto — ¿suficiente para el piso?).

---

## Fase B — El mapa real dentro del simulador

**Meta:** cargar el mapa real en el banco y repetir la batería de pruebas (secciones 1–8) sobre él,
para validar la navegación con geometría realista antes de tocar el robot.

### El hueco clave: raster ↔ segmentos
El simulador **raycast-ea contra SEGMENTOS** (`sim_sensors`), y Cartographer da un **raster** (pgm/
occupancy grid). Hay que salvar esa diferencia. Dos opciones:

| Opción | Qué implica | Pros / Contras |
|---|---|---|
| **B1 · Raycast contra rejilla** | Nuevo camino en `sim_sensors`: castear el láser contra las celdas ocupadas del raster (DDA/Bresenham) en vez de segmentos. Publicar el raster directo como `/map`. | + Fiel al mapa real · − Toca `sim_sensors`, más costoso por rayo |
| **B2 · Vectorizar el pgm** | Convertir el raster a segmentos (detección de contornos/líneas, p.ej. OpenCV `HoughLinesP`) y alimentarlos por `/sim_map` como hoy. | + Reutiliza toda la tubería actual · − Pérdida de fidelidad, tuning del vectorizado |

> Recomendación: **B1** (raycast contra rejilla) — es lo que hará el robot real de todas formas
> (el láser ve el mundo, no segmentos) y evita el arte de vectorizar. B2 queda como atajo si B1 se
> complica.

### Tareas
1. Implementar el camino elegido (B1: `sim_sensors` con raster + `sim_map_grid`/loader que publique
   el pgm como `/map` y `/map_amcl`).
2. Cargar `piso_real` en el banco (nuevo botón/loader "mapa real" en el panel).
3. Re-etiquetar **zonas** sobre el mapa real (cocina/salón/… con `🏷️ área`).
4. Correr las **pruebas 1–8** sobre el mapa real (nav, marcha atrás, sensores, zonas, AMCL, stress).

**Decisiones Fase B:** B1 vs B2; cómo publicar el mapa real en el banco (fichero vs topic).

---

## Fase C — Migración a entorno real + web de observación

**Meta:** navegar de verdad por el piso sobre el mapa generado, y ver el comportamiento en la web.

### C1 · Localización real (no SLAM)
- Para navegar se usa el mapa **guardado** + **AMCL** (localización), no Cartographer (que es para
  *construir*). Alternativa: Cartographer en modo *localization* (pure localization sobre el pbstream).
- **Decisión:** AMCL sobre pgm/yaml **vs** Cartographer-localization sobre pbstream.
- Pose inicial: la cascada ya documentada (última pose / pista 📌 / global) — la `📌 pista` del panel
  ya publica `/initialpose`, reutilizable en real.

### C2 · Bringup de navegación real
- `bringupREAL_nav.sh`: description + HW + EKF + RPLIDAR + **map_server** (carga `piso_real`) + **AMCL**
  + **Nav2** (con `nav2_bench.yaml` **adaptado a real**: revisar radio de giro, footprint, tolerancias,
  velocidades, `collision_monitor` con IR/US reales, no simulados).
- Reemplazar los nodos sim (`sim_motion`, `sim_sensors`, `sim_map_grid`) por la cadena real.

### C3 · Adaptar la web a "observación real"
El panel ya escucha topics estándar, así que el cambio es acotado:
- **Quitar/ocultar** en modo real: dibujar mapa, `▧ obstáculo`, `🌀 deriva`, `📍 real` (son de sim).
- **Mantener:** `/scan` (láser real), `/map` (mapa real), `/amcl_pose`+partículas, `/plan`, coche,
  `◎ destino`/`▶ Ir`, `📌 pista`, zonas, `⚙ Nav2`, `ⓘ nodos`.
- **Añadir:** panel de **estado de sensores reales** (batería/tensión, IR/US crudos, estado del ESC,
  encoders), y un **selector Banco/Real** que cambie el set de controles.
- El refactor de frames recién hecho (mapa fijo, coche salta al corregir) es **justo lo que se quiere
  en real**: verás la corrección de AMCL sobre el mapa real igual que en RViz.

### C4 · Pruebas de navegación real
- Repetir un subconjunto de los casos 1–8 en el piso real: destino simple, puerta, marcha atrás,
  parada de emergencia (IR/US **reales**), ir a zona, robustez de localización al moverse.
- Métricas: error de llegada, nº de replanificaciones, incidentes de colisión evitada.

**Decisiones Fase C:** AMCL vs Cartographer-localization; alcance del rediseño web (modo dual vs panel
aparte); qué parámetros de Nav2 cambian de banco→real.

---

## Riesgos y dependencias transversales
- **Calidad de odometría** (patinaje Ackermann): si el EKF va justo, el SLAM sufre. RF2O (odometría
  láser) puede reforzar la fusión — evaluarlo en A1.
- **Montaje/altura del LIDAR:** oclusiones (muebles bajos, patas de silla) → mapa con huecos.
- **DDS dual-interface** (`ROS_LOCALHOST_ONLY=1`) ya resuelto en el banco — mantenerlo en los bringups.
- **Seguridad física:** primeras pruebas reales con `estop.sh` a mano y velocidades bajas.
- **Diferencia sensores:** el banco tiene láser 360° perfecto; el RPLIDAR real tiene ruido, alcance y
  FoV propios → re-tunear inflado/costmaps y `collision_monitor` con datos reales.

## Orden sugerido
1. **A1** (bringup real + verificar `/scan`, TF, odometría) ← cimiento de todo.
2. **A2–A3** (cartografiar y guardar el piso).
3. **B1** (raycast raster) + cargar el mapa real en el banco + pruebas.
4. **C1–C2** (localización + Nav2 real).
5. **C3** (web observación real) + **C4** (pruebas reales).
