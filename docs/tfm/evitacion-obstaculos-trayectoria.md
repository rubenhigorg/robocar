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

1. **Extender `goto_avoid` a lista de waypoints** (trayectoria completa) con evitación en cada tramo.
2. **Unificar con `path_follower`** en un solo nodo: sigue waypoints + esquiva (y usa **giros en 3
   puntos** para maniobras cerradas si hiciera falta).
3. **Filtro** a los ultrasonidos (mediana / EMA) + **histéresis** para no oscilar al esquivar.
4. Añadir el **LIDAR** al costmap (evitación 360°, obstáculos laterales y dinámicos).
5. Cuando se quiera navegación **con mapa**, migrar a **Nav2** (global planner + local planner +
   costmaps + recovery behaviours). El SLAM ya está (Cartographer), así que hay mapa + localización.
6. Definir/validar el objetivo desde la **web** (Fase 5): dibujar waypoints y ver planificado vs real.

## Ficheros relacionados

- `robocar_pkg`: `obstacle_avoid_node.py`, `goto_avoid_node.py`, `distance_node.py`
  (→ `/ultrasound_data`), `path_follower_node.py`.
- Docs: `plan-validacion-odometria.md`, `nodos-ros2.html` (grafo), `odometria-slam-navegacion.html`.
