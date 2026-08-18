# Evitación de obstáculos en una trayectoria (base para navegación)

Documento de referencia. Captura el diseño, lo implementado y los aprendizajes de la
**evitación reactiva de obstáculos integrada con el seguimiento de una trayectoria**, para
recuperarlo cuando implementemos la navegación completa.

## La idea

Seguir una **trayectoria global** (waypoints / objetivo) y, cuando aparece un obstáculo,
**esquivarlo con una capa local reactiva que tiene prioridad**, y **volver a la trayectoria**
en cuanto se despeja. Es el patrón de **Nav2** (global planner + local controller/costmap) en
versión mínima y sin mapa.

```
        objetivo/waypoints (global)
                 │  go-to-goal (absoluto)
                 ▼
   [ supervisor de prioridad ] ──► /cmd_vel ──► car_control
                 ▲
                 │  override si hay obstáculo
      evitación reactiva (local, ultrasonidos)
```

## Arquitectura

- **Global**: waypoints / objetivo. Se persiguen con **go-to-goal ABSOLUTO** (apuntar a la
  *posición* del objetivo). **Esto es clave para "volver a la trayectoria"**: tras un rodeo, el
  go-to-goal reorienta el robot solo hacia el objetivo. El enfoque *relativo* ("avanza N metros")
  **no sirve** aquí porque un desvío le descuadra la cuenta de distancia.
- **Local**: evitación reactiva **con prioridad**. Si hay obstáculo cerca, sobreescribe el mando
  (gira al lado libre / frena / para). Si no, pasa el mando del go-to-goal.
- **Prioridad** (de mayor a menor): **emergencia IR (parada inmediata)** > evitación ultrasónica
  (esquivar) > trayectoria (go-to-goal). El IR es un "último recurso" de proximidad; los ultrasonidos
  esquivan con antelación; la trayectoria manda cuando todo está despejado.

## Sensores

- **3 ultrasonidos HC-SR04** delanteros (izquierda / centro / derecha) → `/ultrasound_data`
  (`messages_pkg/Distance`: `left_distance`, `center_distance`, `right_distance` en **cm**, +
  `emergency_stop` bool). Publica a ~10 Hz (`distance_node`).
- Rango útil ~2 cm – 3 m; **lectura inválida = −1** (sin eco). Ruido moderado → conviene **filtrar**
  (mediana / EMA) y usar histéresis para no oscilar.
- **Cono estrecho**: un obstáculo fuera del cono no se ve (limitación clave del ultrasonido).
- **IR de proximidad** (GPIO6 → campo `emergency_stop` del msg `Distance`): **parada de emergencia**.
  **Polaridad: `emergency_stop == False` → objeto MUY cerca delante → parar en seco** (idle = True).
  Integrado como **máxima prioridad** en `trajectory_nav_node`/`obstacle_avoid_node` (param
  `emergency_enabled`): si se dispara → `/cmd_vel` a cero inmediato; reanuda al despejarse. Validado.
- **Futuro**: el **LIDAR** (`/scan`) daría evitación 360° y un costmap mucho mejor (obstáculos
  laterales y dinámicos).

## Lógica de evitación reactiva — `obstacle_avoid_node`

- `clean(d)`: −1 o < 2 cm → "lejos" (300) para no disparar en falso.
- **libre** (`center > slow` y lados `> side`) → avanza recto.
- **obstáculo delante** (`center < slow`) → **esquiva** hacia el lado **más libre** (`max(left,right)`),
  velocidad reducida.
- **crítico / encajonado** (`center < stop`, o ambos lados `< side`) → para / gira fuerte.
- Umbrales orientativos (cm): `slow≈70`, `stop≈33`, `side≈25`. **Ajustar según velocidad**: el ESC va
  rápido y **no frena** (rueda por inercia) → hay que **reaccionar pronto** (umbral amplio), no fiarse
  de frenar en seco.
- Parámetro `dry_run` para probar la lógica **sin mover el coche** (imprime la decisión).

## Navegación reactiva — `goto_avoid_node`

- Va a un **objetivo** (`goal_dist` recto desde la pose inicial; **extensible a lista de waypoints**).
- go-to-goal: `err = wrap(atan2(goal − pos) − yaw)`; `w = clamp(kp·err)`; `v = crucero`.
- Evitación con prioridad (misma lógica). Modo `NAV` (sigue trayectoria) vs `ESQUIVA/GIRA/STOP`.
- **Validado en suelo**: `NAV → ESQUIVA` (rodea el obstáculo por el lado libre) `→ NAV` (se re-apunta
  al objetivo, vuelve a la línea) `→ OBJETIVO alcanzado`.

## Seguidor de waypoints con k-turn de reserva — `trajectory_nav_node`

Generaliza `goto_avoid` a una **lista de waypoints** (`/plan_waypoints`, `PoseArray` relativos a la
pose de arranque) y añade el **giro en 3 puntos (k-turn) como reserva** para giros que el go-to-goal
no puede tomar arqueando. Es la base de la web de trayectorias. Prioridad: **emergencia IR > evitación
ultrasónica > trayectoria**.

### ¿Cuándo se activa el k-turn?

El robot Ackermann no puede arquear más cerrado que su **radio de giro mínimo** `R_min` (≈ 0.93 m
calibrado; se usa `r_min = 0.95 m` con margen). Si el waypoint objetivo cae **dentro del círculo de
giro mínimo**, el go-to-goal **no puede alcanzarlo arqueando** → **orbita** alrededor sin llegar.

Chequeo geométrico de **alcanzabilidad** (`reachable()`), en cada ciclo antes de conducir:
1. Se determina a qué lado está el waypoint (producto vectorial rumbo × dirección-al-waypoint).
2. El centro del **círculo de giro** de ese lado está a `R_min` perpendicular al rumbo
   (izq: `centro = pos + R·(−sinθ, cosθ)`; der: el simétrico).
3. Si `dist(waypoint, centro) < R_min` → el waypoint está **dentro del círculo** → **inalcanzable** →
   se activa el **k-turn**. Si está fuera → **go-to-goal** normal.

Es decir: **giros suaves → go-to-goal; giros cerrados (o waypoints casi encima/al lado) → k-turn.**
No se usa el k-turn en todas las situaciones, solo cuando hace falta.

### ¿Cómo funciona el k-turn?

Maniobra de **vaivén** para reorientarse ~en el sitio hacia el waypoint (como un conductor en un
callejón), usando el **yaw** como realimentación:
- Se gira hacia el lado del waypoint (`turn_sign`).
- **Fase FWD**: adelante con dirección al máximo hacia el giro → el yaw avanza.
- **Fase REV**: marcha atrás con **contra-dirección** → el yaw avanza en el **mismo** sentido
  (`yaw_rate = v·tan(δ)/L`: con `v<0` y `δ` contrario, el producto mantiene el signo).
- Cada fase se limita a `kturn_seg_max` (≈ 0.30 m) para caber en poco espacio; al invertir el sentido
  hay una **pausa en neutro** (`neutral_dwell`, el ESC no reversa desde movimiento).
- **Fin del k-turn**: cuando el waypoint vuelve a ser **alcanzable** (`reachable()` = true) → vuelve a
  **go-to-goal**, que arquea el resto. Hay un `kturn_time_max` de seguridad.

En **banco** funciona igual: con el perfil de odometría de **dirección dominante**, el yaw gira por la
dirección + velocidad de rueda (incluso en la reversa), así que las esquinas se completan sin sacar el
coche. Validado en sim (cuadrado 0.8 m: `NAV → K-TURN → … → COMPLETA`, cierre 0.19 m; antes orbitaba).

### Pendiente de optimizar (futuro)

La **activación** del k-turn es mejorable:
- **Histéresis / anti-rebote**: a veces se re-dispara justo tras completar (NAV muy corto entre esquinas).
- **Backstop reactivo**: detectar orbitando (distancia que no converge) como disparo adicional al geométrico.
- **Tuning de `r_min`** y del margen (evitar k-turns innecesarios en giros que sí se pueden arquear).
- Elegir el **sentido de giro** de forma más lista (mínimo nº de maniobras) y decidir *cuánto* girar
  (no solo hasta "alcanzable", sino hasta alinear bien) para reducir el nº de fases.
- Integrar con la **evitación** durante el k-turn (ahora solo la emergencia IR interrumpe el vaivén).

## Aprendizajes / gotchas

- El **go-to-goal absoluto** es lo que permite "volver a la trayectoria" tras el rodeo.
- **ESC/drivetrain**: velocidad mínima alta (~0.3+ m/s), el neutro **no frena** (inercia), la rampa de
  seguridad de `car_control` tarda ~1 s → **reaccionar pronto**; no hay crawl fino ni frenada seca.
- **Odometría fiable** (~±1.5% / ~2 cm a 30 Hz, tras arreglar el encoder) es la **base** — sin ella el
  go-to-goal no funciona.
- **Ultrasonidos**: ruidosos y cono estrecho → filtrar; para evitación seria, LIDAR.
- **Armado** del modo autónomo intermitente por el mando (`/joy` sobre rosbridge); a veces hay que
  armar por `/joy` desde la Pi.

## Camino a la navegación completa (cuando implementemos nav)

1. ~~Extender a lista de waypoints~~ **HECHO** (`trajectory_nav_node`).
2. ~~Unificar go-to-goal + k-turn~~ **HECHO** (`trajectory_nav` = go-to-goal + k-turn de reserva +
   evitación + emergencia). Pendiente: **optimizar la activación del k-turn** (ver sección arriba).
3. **Filtro** a los ultrasonidos (mediana / EMA) + **histéresis** para no oscilar al esquivar.
4. Añadir el **LIDAR** al costmap (evitación 360°, obstáculos laterales y dinámicos).
5. Cuando se quiera navegación **con mapa**, migrar a **Nav2** (global planner + local planner +
   costmaps + recovery behaviours). El SLAM ya está (Cartographer), así que hay mapa + localización.
6. Definir/validar el objetivo desde la **web** (Fase 5): dibujar waypoints y ver planificado vs real.

## Ficheros relacionados

- `robocar_pkg`: `obstacle_avoid_node.py`, `goto_avoid_node.py`, `distance_node.py`
  (→ `/ultrasound_data`), `path_follower_node.py`.
- Docs: `plan-validacion-odometria.md`, `nodos-ros2.html` (grafo), `odometria-slam-navegacion.html`.
