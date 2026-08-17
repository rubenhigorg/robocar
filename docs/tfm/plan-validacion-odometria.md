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

### Fase 3 — Velocidad lenta por pulsos *(mejora de observación)*
- [ ] Modo "crawl" a pulsos (micro-impulsos + inercia) para bajar del umbral del ESC.
- [ ] Calibrar duty/periodo para una velocidad media baja estable.

### Fase 4 — Evitación de obstáculos (reactiva)
- [ ] Verificar sensores: 3 ultrasonidos (`/ultrasound_data`) + **aclarar los IR** (pin 6 = `emergency_stop`;
  ¿otros IR? ¿integrarlos?).
- [ ] Capa de seguridad con prioridad: obstáculo < umbral → frenar/pausar; reanudar al despejar.
- [ ] Evitación activa: sesgar dirección hacia el lado libre (ultrasonido izq/centro/der) y retomar.

### Fase 5 — Soporte web (generar + validar trayectorias)
- [ ] Generalizar `path_follower` a una **lista de waypoints** por topic/servicio (no solo cuadrado);
  elegir por tramo giro suave (arco) o cerrado (k-turn) según el ángulo.
- [ ] Web: lienzo para **dibujar waypoints / elegir forma** + parámetros → enviar por rosbridge.
- [ ] Tras ejecutar: **planificado vs real** + resultado de validación en la web; estado en vivo.

## Dependencias

- Fase 1 antes de validar nada con reversa (2.2 y la parte k-turn de la web).
- Fases 3 y 4 son independientes.
- La web (5) se apoya en 1, 2 y en generalizar el nodo.
