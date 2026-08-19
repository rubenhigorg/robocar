# De cero: nodos, topics, TF y Nav2

Recorrido desde el principio por los conceptos base de ROS2 aplicados al robocar, pensado
para reconstruir el mapa mental sin dar nada por supuesto. Se lee de arriba abajo; cada
sección se apoya en la anterior.

**El trío base de ROS2:** **nodos** que **publican / se suscriben** a **mensajes** en **topics**.
Todo lo demás (incluido TF y Nav2) es ese mismo trío aplicado.

---

## 1. ¿Qué es un nodo?

Un robot con ROS2 **no es un solo programa gigante**. Es un montón de **programas pequeños**,
cada uno con **una tarea**, corriendo a la vez y hablando entre ellos. Cada uno se llama **nodo**.

Analogía: una **cocina de restaurante**. No hay un cocinero que lo haga todo; hay uno para las
verduras, otro para la carne, otro para los postres. Un nodo es cada cocinero.

Nodos reales del robocar:

| Nodo | Su única tarea |
|---|---|
| `sim_motion` | Convertir las órdenes de movimiento en la posición del coche |
| `sim_sensors` | Simular el LIDAR y los ultrasonidos |
| `sim_map_grid` | Generar el mapa de ocupación |
| `car_control` | Mover el servo de dirección y el motor (hardware) |
| `trajectory_nav` | Decidir hacia dónde ir |

`ros2 node list` = **la lista de cocineros trabajando ahora mismo**.

> **Idea clave:** un nodo = un programa = una tarea. El robot funciona porque muchos nodos
> trabajan a la vez.

---

## 2. ¿Cómo hablan los nodos? — Topics

Los nodos **no se hablan directamente**. Lo hacen a través de **topics** (canales).

Analogía: **cintas transportadoras** con una etiqueta. El cocinero de verduras *deja* cosas en
la cinta `"verduras cortadas"`; el del plato final *coge* de esa cinta. No se hablan; usan la
cinta. Un **topic es esa cinta con nombre** (se escriben con `/`: `/cmd_vel`, `/scan`, `/map`).

Dos papeles respecto a una cinta:

- **Publicar** (*publish*) = **dejar** datos en la cinta. Quien publica no sabe quién recogerá.
- **Suscribirse** (*subscribe*) = **coger** los datos que llegan; el nodo reacciona a cada uno.

Ejemplo real (las órdenes de movimiento):

```
trajectory_nav  ──publica──▶  /cmd_vel  ──lo recibe──▶  sim_motion
  (decide a dónde ir)         (la cinta)        (mueve el coche)
```

Los dos nodos **nunca se conocen**; solo comparten el nombre de la cinta. Por eso se puede
**cambiar un nodo por otro** sin tocar el resto: el día que metamos Nav2, publicará en
`/cmd_vel` en vez de `trajectory_nav`, y `sim_motion` ni se entera. **Esta es la base de todo
el diseño del banco.**

Comandos:
```
ros2 topic list              # todas las cintas que existen ahora
ros2 topic echo /cmd_vel     # asómate y mira qué pasa por esa cinta en vivo
ros2 topic info /cmd_vel     # cuántos nodos publican y cuántos escuchan
```

> **Idea clave:** los nodos no se hablan directamente; **publican** y **se suscriben** a
> **topics**. Publicar = dejar, suscribirse = coger.

---

## 3. ¿Qué viaja por la cinta? — Mensajes y tipos

Por una cinta no viaja información a lo loco: viaja un **paquete con forma fija**, el **mensaje**.
Su forma se llama **tipo de mensaje**.

Analogía: **impresos oficiales**. El impreso "solicitud de vacaciones" tiene siempre las mismas
casillas. El **tipo** es el modelo de impreso; el **mensaje** es un impreso ya rellenado.
**Cada cinta transporta un solo tipo de impreso.**

Ejemplos reales:

**`/cmd_vel`** → tipo **`Twist`** (orden de movimiento):
```
linear.x   →  velocidad hacia delante   (ej. 0.3 m/s)
angular.z  →  cuánto girar               (ej. 0.4 = a tope a la izquierda)
```

**`/odometry/filtered`** → tipo **`Odometry`** (dónde está el coche):
```
pose.position.x, y   →  posición
pose.orientation     →  hacia dónde mira
twist                →  a qué velocidad va
```

**`/scan`** → **`LaserScan`** (una vuelta del LIDAR: distancias por ángulo).
**`/map`** → **`OccupancyGrid`** (rejilla de celdas: pared=100, libre=0).

Los dos extremos de una cinta deben **estar de acuerdo en el tipo**. Por eso en la web:
```js
send({op:'subscribe', topic:'/map', type:'nav_msgs/msg/OccupancyGrid'})
```

Comandos:
```
ros2 topic type /cmd_vel                       # qué tipo lleva esa cinta
ros2 interface show geometry_msgs/msg/Twist    # las casillas de ese impreso
```

> **Idea clave:** por la cinta viajan **mensajes**; cada uno tiene un **tipo** (casillas fijas);
> cada cinta lleva un solo tipo.

---

## 4. ¿Desde dónde se mide? — Frames (sistemas de coordenadas)

Una posición **no significa nada** sin decir **desde qué punto de referencia** se mide. "El coche
está en `x=1.2, y=0.3`"... ¿medido **desde dónde**?

Analogía — *"¿dónde estás?"*: *"a 2 m de la puerta"* / *"en el asiento 14F"* / *"en la calle
Mayor 5"*. **Eres el mismo punto**, pero las coordenadas cambian según **desde dónde midas**.
Ese "desde dónde" es un **frame**: un **origen** (el 0,0) + una **orientación** (hacia dónde
apunta la X, la Y).

Frames del robocar:

- **`base_link`** = *"desde el coche mismo"* (origen en el centro del eje trasero). En este frame
  **el coche está siempre en (0,0)**. Lo que tiene coordenadas aquí es lo montado en él: el LIDAR
  está en `(0.070, 0, 0.028)` respecto a `base_link`.
- **`laser`** = *"desde el sensor LIDAR"*. Cuando dice "algo a 1 m", es desde el laser.
- **`odom`** = *"desde donde el coche arrancó"*. Aquí el coche **sí se mueve** (0,0 → 1.2,0.3 → ...).
- **`map`** = *"desde un punto fijo del mundo"* (una esquina del piso). No se mueve nunca.

**El mismo punto físico tiene coordenadas distintas en cada frame.** Una pared que el LIDAR ve
justo delante:
```
  en 'laser'      →  (1.0, 0)      "a 1 m delante del sensor"
  en 'base_link'  →  (1.07, 0)     "a 1.07 m del centro del coche" (el laser va 7 cm alante)
  en 'odom'       →  (2.2, 0.3)    "respecto a donde arrancó"
  en 'map'        →  (5.4, 1.1)    "en tal esquina del piso"
```
Es la misma pared; solo cambia **desde dónde la miras**. El problema: el LIDAR da cosas en
`laser`, pero el mapa las quiere en `map`. Alguien tiene que **traducir**. Eso es **TF**.

> **Idea clave:** un **frame** es un "desde dónde mido". El mismo punto vale distinto en cada
> frame. El robocar usa `laser`, `base_link`, `odom`, `map`.

---

## 5. El traductor entre frames — TF

**TF** (de *TransForms*) es el sistema de ROS2 que traduce coordenadas de un frame a otro.

La pieza básica es una **transformada**: la **receta para pasar de un frame a otro** = un
**desplazamiento + un giro**. Ejemplo del robocar:
```
base_link → laser :  desplázate (0.070, 0, 0.028) y gira 180°
```
(*"el laser está 7 cm delante del centro del coche, 2.8 cm arriba, y mirando al revés"*.)

Dos tipos de recetas, y son **topics normales**:

- **Fijas** (`/tf_static`): nunca cambian (el laser está atornillado). Se publican **una vez**.
  Salen del **URDF** vía `robot_state_publisher`.
- **Que cambian** (`/tf`): se mueven. `odom→base_link` cambia porque el coche se mueve;
  `sim_motion` la publica **50 veces por segundo**.

**Lo potente: TF encadena recetas.** No tienes la receta directa `laser→map`, pero TF tiene los
eslabones (`laser → base_link → odom → map`) y los **encadena solo**. Le preguntas *"este punto
en `laser`, ¿cuánto vale en `map`?"* y recorre la cadena. **Eso es lo que hace Nav2** para pintar
cada eco del LIDAR en el mapa. (Como traducir español→japonés pasando por inglés.)

**El tiempo:** TF guarda cada receta **con su hora**, para poder decir *dónde estaba el laser
respecto al mapa en el instante exacto de la medida* (y no mezclar una medida vieja con una
posición nueva).

Comando:
```
ros2 run tf2_ros tf2_echo base_link laser   # "dame la receta de base_link a laser"
```

> **Idea clave:** TF traduce coordenadas entre frames. Cada **transformada** es una receta
> (desplazar + girar); las fijas en `/tf_static`, las que cambian en `/tf`. TF **encadena**
> recetas.

---

## 6. El árbol TF del robocar

Los frames forman un **árbol** (como un árbol genealógico): cada frame **cuelga de un padre**.

```
        map                    ← punto fijo del mundo
         │   (map→odom)
        odom                   ← donde el coche arrancó
         │   (odom→base_link)   ← cambia 50 veces/s
      base_link                ← el coche (centro eje trasero)
      ┌──┼──────┬──────┬─────────────┐
   laser  base_  imu  ruedas  ultrasonidos     ← todos FIJOS (atornillados)
          footprint
```

Quién publica cada eslabón:

| Receta (eslabón) | Quién la publica | ¿Cambia? |
|---|---|---|
| `map → odom` | `sim_map_grid` (banco, identidad) / real: el SLAM | fija |
| `odom → base_link` | `sim_motion` (la odometría) | **sí, 50 Hz** |
| `base_link → laser`, `→ ruedas`, `→ imu`... | `robot_state_publisher` (del URDF) | fijas |

**La regla de oro:** cada frame tiene **un solo padre** (como cada persona tiene un padre
biológico). Así hay **un único camino** entre dos frames y TF siempre sabe cómo encadenar.

### El bug real de `base_footprint` (y su arreglo)

El URDF decía `base_footprint → base_link` (footprint = padre), pero `sim_motion` publica
`odom → base_link`. Resultado: **`base_link` con DOS padres** → rompe la regla → el árbol se
**parte en dos**:
```
  trozo 1:  odom → base_link → laser ...      ✅ resolvía
  trozo 2:  base_footprint → base_link        ❌ suelto
  → "odom → base_footprint" daba: "two unconnected trees"
```
**Arreglo:** invertir el eslabón para que `base_footprint` sea **hijo** de `base_link`:
```
Antes:  base_footprint → base_link      (2 padres → roto)
Ahora:  base_link → base_footprint      (base_link con 1 padre: odom → ✅)
```
Un solo árbol `map → odom → base_link → { base_footprint, laser, imu, ruedas, ultrasonidos }`.
(En el URDF: `base_footprint_joint` con `parent=base_link`, `child=base_footprint`,
`z=-wheel_radius`.)

> **Idea clave:** los frames forman un **árbol** con **un solo padre** por frame. El bug era
> `base_link` con dos padres; el arreglo puso `base_footprint` de hijo → árbol único.

---

## 7. Cómo encaja todo — Nav2

**El objetivo:** decirle al coche *"ve ahí"* y que **él solo** calcule el camino, lo siga y
esquive paredes. Quien hace eso es **Nav2** — no un nodo, sino un **conjunto de nodos** de
navegación.

### Qué necesita Nav2 (sus entradas) — y por qué construimos cada cosa

| Necesita... | ...que en el robocar es | Lo aporta |
|---|---|---|
| El **mapa** (dónde están las paredes) | `/map` (`OccupancyGrid`) | `sim_map_grid` |
| Los **obstáculos en vivo** | `/scan` (`LaserScan`) | `sim_sensors` |
| Saber **dónde está** | `/odometry/filtered` + **árbol TF** | `sim_motion` + `robot_state_publisher` |
| Un **destino** | `/goal_pose` | *(pendiente — la web)* |

### Qué produce Nav2 (su salida)

- **Planifica** la ruta con el `/map` (camino de A→B rodeando paredes).
- **Conduce**: suelta órdenes de movimiento siguiendo el camino, respetando la cinemática y
  esquivando lo que aparezca en `/scan`.
- **Salida:** publica en `/cmd_vel` — **la misma cinta de siempre**.

### El lazo completo

```
        tú/LLM: "ve ahí"
             │  /goal_pose
             ▼
        ┌─────────┐   /map (sim_map_grid) ──┐
        │  Nav2   │   /scan (sim_sensors) ──┤ entradas
        │ planea+ │   TF + /odometry ───────┘
        │ conduce │
        └────┬────┘
             │  /cmd_vel
             ▼
        sim_motion  ──▶  mueve la pose  ──▶  /odometry/filtered
             │                                      │
             └──── sim_sensors ve el mapa desde ────┘
                   la nueva pose → /scan → (vuelta a Nav2)
```

Es un **círculo** a 30-50 Hz: Nav2 manda `/cmd_vel` → `sim_motion` mueve el coche →
`sim_sensors` ve el mapa desde la nueva posición → Nav2 recibe el nuevo `/scan` y `/odometry`
→ corrige → vuelve a mandar `/cmd_vel`.

### La idea que da sentido al diseño

Hoy **quien conduce es `trajectory_nav`** (apaño casero) y **la ruta la dibujas tú**. Es un
**andamio temporal**. El plan es **quitar `trajectory_nav` y poner Nav2**. Como todos hablan por
las **mismas cintas**, al hacer el cambio **nada más se entera**. Y lo mismo para pasar del banco
a la realidad: `sim_motion`→el coche real, `sim_sensors`→el LIDAR real; **Nav2 no cambia**. Por
eso el banco tiene que "hablar las mismas cintas": para ser un **ensayo idéntico** a la realidad.

---

## Recapitulación

1. **Nodo** = un programa, una tarea (cocinero).
2. **Topic** = cinta con nombre; los nodos **publican** (dejan) y **se suscriben** (cogen).
3. **Mensaje** = el impreso que viaja; su **tipo** = el modelo de impreso (casillas fijas).
4. **Frame** = "desde dónde mido". El mismo punto vale distinto en cada frame.
5. **TF** = traductor entre frames; cada **transformada** es una receta (desplazar + girar); TF
   las **encadena**.
6. **Árbol TF** = frames colgando de un padre único; `map→odom→base_link→laser`.
7. **Nav2** = planea + conduce; consume `/map`, `/scan`, TF, `/odometry`, `/goal_pose` → produce
   `/cmd_vel`.

## Chuleta de comandos

```
ros2 node list                                 # nodos corriendo
ros2 topic list                                # topics (cintas) existentes
ros2 topic echo  <topic>                       # ver los mensajes en vivo
ros2 topic info  <topic>                       # nº de publicadores / suscriptores
ros2 topic hz    <topic>                       # frecuencia de publicación
ros2 topic type  <topic>                       # tipo de mensaje del topic
ros2 interface show <tipo>                      # casillas de un tipo de mensaje
ros2 run tf2_ros tf2_echo <frame_a> <frame_b>   # receta TF entre dos frames
```

## Dónde encaja esto en el proyecto

Este documento cubre los **fundamentos** (Capa 0) que sostienen todo lo demás. El banco de
simulación (preparatoria de la Capa 2, Nav2) está montado sobre estas piezas: ver
[Roadmap](roadmap.md), [Mapa de nodos ROS2](nodos-ros2.html) y
[Odometría, SLAM y navegación](odometria-slam-navegacion.html).
