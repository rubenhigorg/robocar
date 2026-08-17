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

### Fase 1 — Encoder con sentido *(desbloquea la validación con reversa)* — **EN CURSO**
- [ ] `encoder_node` firma `/wheel_speed` según el signo del último `/cmd_vel`.
- [ ] Validación out-and-back: recto **+1 m y luego −1 m** → la odometría vuelve a ~0
  (hoy daría ~2 m). Objetivo: |error| pocos cm.

### Fase 2 — Protocolo de validación de odometría *(el corazón)*
- [ ] Trayectorias patrón **solo hacia delante** (recto N m, rectángulo grande, círculo):
  medir con cinta el resultado real vs odometría → error absoluto y **por metro (%)**.
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
