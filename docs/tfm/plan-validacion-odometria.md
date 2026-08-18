# Plan: validación de odometría con trayectorias, obstáculos y web

Documento de trabajo. Objetivo global: **generar trayectorias correctas, ejecutarlas y
validar la odometría** con ellas; después, esquivar obstáculos y poder definir/validar
trayectorias desde la web.

## Hallazgos que condicionan el plan

- **El encoder no tiene sentido de giro** (rueda dentada de un solo canal → `/wheel_speed`
  siempre ≥ 0). En marcha atrás la odometría cuenta el retroceso como avance, así que
  **hoy no se puede validar ninguna trayectoria con reversa**. Es el primer bloqueo a resolver.
- **Umbral de velocidad del ESC alto**: por debajo de ~0.2 m/s (throttle casi en neutro) el
  motor se cala; no hay crawl suave con throttle constante. Para ir más lento → pulsos.
- **Ackermann, radio de giro grande (~0.7–0.8 m)**: un cuadrado de 1 m es más cerrado de lo
  que el coche gira hacia delante → hacen falta **giros en 3 puntos** (con marcha atrás) para
  trayectorias cerradas.

## Estado del seguidor de trayectoria (base ya hecha)

- `path_follower_node` con dos comportamientos:
  - *persecución de puntos* (go-to-goal): bien para trayectorias suaves.
  - *giros en 3 puntos* (k-turn, con reversa): cierra esquinas cerradas. Validado en simulación
    (cierre 0.29 m) y ejecutado en suelo (secuencia completa; el cierre por odometría no es fiable
    por el problema del encoder → Fase 1).

---

## Fases

### Fase 0 — Consolidar la base
- [x] `path_follower_node` (2 modos) validado en sim + suelo.
- [x] Deadman del mando (no publica en reposo → no compite con rutas autónomas).
- [x] Este plan en el repo.

### Fase 1 — Encoder con sentido + reversa fiable + tiempo real — **EN CURSO**
- [x] `encoder_node` firma `/wheel_speed` con el signo del último `/cmd_vel` (`use_cmd_direction`).
- [x] **Pausa en neutro antes de invertir el sentido** (el ESC BLHeli no reversa desde
  movimiento: frena). Implementado en `path_follower` (`_drive` + `neutral_dwell`) y en las
  maniobras. **Validado en suelo: la marcha atrás ya funciona de verdad.**
- [ ] **Encoder en TIEMPO REAL (bloqueante para todo lo demás).** El Arduino (I2C 0x08) solo
  expone la cuenta de la última ventana de **1 s** (1 Hz, ~1 s de latencia); no hay contador
  acumulativo (registros 2–15 = 0xFF). Con eso la odometría no sirve para control en tiempo
  real ni para medir maniobras rápidas. Opciones:
  - **(A) Reprogramar el Arduino** (0x08, exclusivo del encoder): contar pulsos por interrupción
    y exponer un **contador acumulativo de 32 bits**; `encoder_node` lo lee a 20–50 Hz y deriva
    la velocidad (baja latencia). Requiere el tipo de placa + pin del encoder y **flasheo por USB
    desde un portátil** (el Arduino no está por USB a la Pi).
  - **(B) Llevar la señal del encoder a un GPIO de la Pi** y contar en la Pi (p.ej. `pigpio`,
    flancos con marca de tiempo hardware) a alta frecuencia. Requiere recableado y comprobar
    niveles 5 V/3.3 V.
- [x] **RESUELTO (opción A)**: firmware nuevo del Nano (`firmware/nano_encoder/enc_fw.ino`):
  contador acumulativo de 16 bits por interrupción (D2/INT0), leído por I2C 0x08. `encoder_node`
  v2 lo lee a **30 Hz** y deriva la velocidad (delta/dt) → `/wheel_speed` a 30 Hz (antes 1 Hz).
  Flasheado desde la Pi con `arduino-cli` por USB. Se usa transacción de 2 bytes (fiable con el
  I2C de la Pi). Calibración provisional 143.8 pulsos/vuelta (afinar por distancia en Fase 2).
- [ ] Revalidar el signo/latencia con un out-and-back **largo** y **calibrar m/pulso por distancia**.

### Fase 2 — Protocolo de validación de odometría *(el corazón)*
- [x] **Escala en recto validada (~±1.5%)**. Dos ensayos: con 0.001446 dio +1.8% (odom 1.908
  vs real 1.875); con 0.001421 dio −1.4% (odom 1.991 vs real 2.02). Ambos encierran el valor
  real; estimador combinado **`meters_per_pulse = 0.001432`** (fijado). El residual ~1.5% es
  **ruido de medir a mano** (cinta ±5-10 mm, inercia del ESC en neutro, alineación), no del
  sensor. Odometría a 30 Hz, en tiempo real.
- [x] **Ground-truth cerrado CON reversa validado**: out-and-back (ida 0.98 m + pausa neutro +
  vuelta) → cierre odometría 0.608 m vs real 0.63 m → **~2 cm de error** (~1.6% del recorrido
  total, igual que la escala en recto). La odometría rastrea bien incluso con cambio de sentido.
- [x] Cuadrado k-turn 0.8 m ejecutado y trazado fielmente (cierre odom ~0.25–0.34 m). Nota: el
  k-turn necesita **más área que el lado nominal** (la reversa sobresale) — en 1.2×1.2 m topa la
  pared; usar out-and-back o cuadrado más pequeño / `kturn_seg_max` menor.
- [ ] (Opcional) más patrones (rectángulo, círculo) para apurar el promedio.

**Conclusión Fase 2: odometría validada a ~±1.5% / ~2 cm, en tiempo real (30 Hz), en recto y
en trayectoria cerrada con reversa.**
- [ ] Con encoder firmado, validar trayectorias **con reversa** (cuadrado k-turn): cierre real vs odometría.
- [ ] Métricas registradas (cierre, deriva/m, error de rumbo) + gráficas planificado-vs-real.

### Fase 3 — Velocidad lenta *(cerrada: límite de hardware)*
- [x] **Veredicto: no se puede hacer crawl fino con este drivetrain.** El brushless + ESC BLHeli
  tiene velocidad mínima alta (~0.3+ m/s), el neutro **no frena** (rueda por inercia) y la rampa
  de seguridad de `car_control` tarda ~1 s en enganchar el throttle. Probado un crawl por saltos
  controlados por odometría: cada "salto de 8 cm" acaba en ~0.3 m (acelera y rueda). El freno por
  micro-reversa ayuda poco (la rampa también lo retrasa ~0.5 s).
- Lo viable: **modo "a tirones"** (~0.3 m por salto + pausa), más lento/observable que el continuo.
- Crawl fino de verdad = **hardware** (motor/ESC brushed, reductora, o ESC sensored). Fuera de alcance
  ahora. `crawl_test.py` queda como demo del modo a tirones.

### Fase 4 — Evitación de obstáculos (reactiva) — **núcleo hecho**
- [x] Sensores: 3 ultrasonidos `/ultrasound_data` (msg `Distance`: left/center/right en **cm** +
  `emergency_stop` bool GPIO6). Los 3 funcionan (~10 Hz). El "IR" no está integrado como topic
  aparte (GPIO6 = emergency_stop, idle=True). Ruido ultrasónico moderado (pendiente filtro).
- [x] **`obstacle_avoid_node`**: evitación reactiva pura. Libre→avanza; center<slow→esquiva hacia el
  lado más libre (compara left/right); center<stop o encajonado→para/gira. `dry_run` para probar la
  lógica sin mover. Validado (objeto a 11 cm→GIRA correcto; en marcha esquiva ampliamente).
- [x] **`goto_avoid_node`**: navegación reactiva = **global (go-to-goal absoluto) + local (evitación
  con prioridad)**. Va a un objetivo recto; si aparece obstáculo lo rodea y **se re-apunta al objetivo
  → vuelve a la trayectoria**. Validado: NAV→ESQUIVA→NAV→OBJETIVO alcanzado (2 m). Patrón Nav2 mínimo.
- [ ] (Siguiente) filtro a los ultrasonidos; extender a **lista de waypoints** (trayectoria completa)
  con evitación; unificar con `path_follower`.

### Fase 5 — Soporte web (generar + validar trayectorias)
- [x] **`trajectory_nav_node`**: seguidor de **lista de waypoints** (`/plan_waypoints`, `PoseArray`,
  relativos a la pose de arranque) con go-to-goal + evitación (generaliza `goto_avoid`). Publica
  estado en `/trajectory_nav/status`. Validado en simulación (cuadrado de 4 waypoints, cierre 0.19 m).
- [ ] Web: lienzo para **dibujar waypoints / elegir forma** + parámetros → publicar el PoseArray por rosbridge.
- [ ] Tras ejecutar: **planificado vs real** + resultado de validación en la web; estado en vivo (topic status).

## Odometría por ángulo de dirección + perfiles (modelo bicicleta)

- **`steer_yaw_node`**: de `/wheel_speed` (v) y `/cmd_vel` (δ desde `angular.z`) calcula
  `yaw_rate = v·tan(δ)/L` (modelo bicicleta) → `/steer_yaw_cov` (TwistWithCovariance, solo vyaw).
  Fusionado en el EKF como **`twist1`**, compite con la IMU (`imu0`). `tan_max = L/R_min ≈ 0.233`
  (de R_min ~0.75 m; afinable contra la IMU en suelo).
- **Perfiles = la covarianza `yaw_variance`** (el peso). IMU tiene var 0.0004:
  - **Suelo**: `yaw_variance` alta (p.ej. 0.5) → peso despreciable, manda la IMU (odometría validada intacta).
  - **Banco**: `yaw_variance` baja (p.ej. 0.00002) → **la dirección domina** → la odometría GIRA aunque la
    IMU esté plana (el robot no se mueve). Validado: yaw +166° en 4 s conduciendo con giro en el banco.
- **Uso**: para probar giros/recorridos EN BANCO sin sacar el coche. Nota: el go-to-goal sigue sin poder
  cerrar esquinas más cerradas que R_min (0.75 m) — orbita; para cuadrados cerrados, k-turn (`path_follower`).

## Dependencias

- Fase 1 antes de validar nada con reversa (2.2 y la parte k-turn de la web).
- Fases 3 y 4 son independientes.
- La web (5) se apoya en 1, 2 y en generalizar el nodo.
