# Del banco a la realidad: qué cambia de la simulación al mundo real

Documento de estudio de la **migración sim → real**: qué del banco de simulación se traslada
tal cual, qué eran **espejismos**, y qué problemas nuevos aparecen al conducir un robot físico por
un piso real. Es el marco conceptual de la [Capa 1](plan-capa1-mapa-real.md).

---

## 1. Por qué un banco (simulación) primero

El **banco** es una **capa preparatoria**: reproduce la arquitectura ROS2/Nav2 completa pero con
sensores y motor **simulados** (nodos `sim_sensors`, `sim_motion`, `sim_map_grid`). Sirve para
desarrollar y validar **todo el software** —planificación, control, localización, la web, el contrato
de configuración para el LLM— **sin riesgo físico** y sin depender de tener el robot montado y con
batería. La idea: llegar al mundo real con la lógica ya probada, para que allí solo quede pelear con
lo que de verdad es distinto (el hardware y la física).

## 2. Lo que el banco valida de verdad (y migra tal cual)

Estas piezas son **idénticas** en banco y en real —el banco las ejercita de verdad:

- **El stack de Nav2**: planner (Smac Hybrid-A\* car-like), controller (RPP), costmaps,
  `collision_monitor`, `behavior_server`, lifecycle. Misma config (`nav2_bench.yaml`), mismos topics.
- **La web** (`trayectorias.html`, `cartografia.html`, mando): habla por topics estándar
  (`/scan`, `/map`, `/odometry/filtered`, `/amcl_pose`, `/goal_pose`, `/cmd_vel`). Da igual quién los
  produzca. El **refactor de frames** (mapa fijo, el coche salta al corregir) es *justo* lo que se
  quiere en real.
- **El contrato de topics/TF**: `map → odom → base_link → laser`, `/cmd_vel`, `/goal_pose`…
- **La localización (AMCL)** como concepto y su integración; el **contrato `/nav_config`** para el LLM.

> Conclusión: el banco valida la **capa de software**. Lo que migra es esa capa; lo que cambia está
> **por debajo** (de dónde salen los datos) y **alrededor** (la física).

## 3. Los espejismos del banco (lo que NO es real)

Lo que el banco te da "gratis" y en la realidad hay que ganarse:

| Espejismo del banco | Realidad |
|---|---|
| **Láser perfecto 360°** casteado de una pose verdadera | RPLIDAR C1 real: ruido, alcance/FoV limitados, **oclusiones** (muebles bajos, patas de silla), reflejos, vibración del motor |
| **Odometría perfecta** (`sim_motion` integra `cmd_vel` exacto) | EKF (encoders+IMU+rf2o) con **deslizamiento**, deriva y **derrapes**; nunca es exacta |
| **Pose verdadera** (`/truth_pose`) siempre disponible | **No existe ground-truth**: nunca sabes exactamente dónde estás; solo la estimas |
| **Sin colisiones** (el robot atraviesa paredes si el costmap no lo para) | Choques reales, con consecuencias; fricción, umbrales, alfombras |
| **Mapa "dibujado"** perfecto y cuadrado | Mapa **construido por SLAM**: torcido si arrancas mal, con fugas y ruido; hay que limpiarlo |
| **Reinicio instantáneo** a un estado limpio | Batería, arranque de sensores, calibración del giróscopo, cableado |

El propio banco lo avisa: activando `🌀 deriva` deja de mentir sobre la odometría, y ahí se ve por qué
**AMCL es imprescindible en real** (ver [Localización y AMCL](localizacion-amcl.md)).

## 4. Comparativa por subsistema

| Subsistema | Banco (sim) | Real |
|---|---|---|
| **Láser** | `sim_sensors` castea 360° desde `/truth_pose` | `rplidar_ros` → RPLIDAR C1 por UART, frame `laser` (montado 180°), 10 Hz |
| **Ultrasonidos / IR** | casteados perfectos | HC-SR04 / IR por I2C: ruido, *crosstalk*, puntos ciegos |
| **Odometría** | `sim_motion` (perfecta, o con deriva simulada) | `ekf_node` fusiona `encoder` (I2C) + IMU MPU6050 + `rf2o` (láser) |
| **Localización** | AMCL sobre mapa dibujado | AMCL sobre mapa **guardado**, o Cartographer-localization sobre pbstream |
| **Mapa** | `/sim_map` (segmentos) → `sim_map_grid` | **Cartographer** (SLAM) → `/map`, luego `.pgm` limpiado a mano |
| **Motor / dirección** | `sim_motion` mueve un robot virtual al instante | `car_control_node` → ESC + servo (I2C PCA9685): inercia, latencia, deadman, **freno del ESC al invertir** |
| **Cinemática** | Ackermann ya modelado (R_min=0.93) | Ackermann real: no gira en el sitio, radio real, patina |
| **Física** | ninguna (mundo ideal) | fricción, derrapes, colisiones, suelo irregular |
| **CPU** | nodos sim ligeros | drivers reales + SLAM + Nav2 sobre la Pi4 (hay que vigilar carga) |

## 5. Lo que SOLO se puede validar en el mundo real

El banco no puede tocar esto —hay que probarlo con el robot en el suelo:

- **Calidad de la odometría** bajo deslizamiento real (el banco con ruedas al aire ni la ejercita).
- **Manejo del ruido** del láser/US/IR reales por los costmaps y `collision_monitor`.
- **Localización real**: convergencia de AMCL, deriva real, re-localización al moverse.
- **Dinámica del motor**: rampas, freno del ESC, respuesta del servo, hombre-muerto.
- **Colisiones y derrapes**: el gran problema del SLAM Ackermann (→ checkpoints, [plan A4](plan-capa1-mapa-real.md)).
- **Timing bajo carga real** en la Pi4.
- **Re-tuneo de Nav2**: inflado, velocidades, `collision_monitor` con IR/US **reales** (en el banco el
  láser 360° hace la esquiva de US redundante; en real no).

## 6. La cadena de nodos: sim → real (qué se reemplaza)

Migrar = **quitar los nodos sim y poner la cadena real**, dejando intacto Nav2 + web:

```
BANCO:  sim_motion ─┐                       REAL:  encoder + IMU ─► ekf_node ─► /odometry/filtered
        sim_sensors ─┼─► /scan, /odom, TF          rplidar_ros ───► /scan
        sim_map_grid ┘   /map                      cartographer ──► /map, TF map→odom
                                                    car_control ───► ESC/servo (de /cmd_vel)
        (Nav2 + web + AMCL: SE MANTIENEN)          (Nav2 + web: SE MANTIENEN)
```

El bringup lo materializa: `bringupNAV2.sh` (banco) vs `bringupSLAM.sh` / futuro `bringupREAL_nav.sh`
(real). Mismos topics de salida → Nav2 y la web ni se enteran de quién los produce.

## 7. Riesgos nuevos del mundo físico

- **Derrapes** → mapa inválido. Mitigado con **checkpoints + reanudación en la pose** del robot.
- **Colisiones** → daño real. Primeras pruebas a **velocidad baja**, con `estop.sh` a mano y supervisión.
- **Deriva de odometría** → sin AMCL, el robot se pierde. AMCL pasa de "opcional" (banco) a **crítico**.
- **Batería / alimentación** → caídas de tensión afectan a los servos y a la Pi.
- **Montaje del LIDAR** → oclusiones y altura mal elegida = mapa con huecos.

## 8. Estrategia de migración (resumen)

1. **Cartografiar** el piso real con Cartographer conduciendo (Fase A) → mapa `.pgm` limpiado.
2. **Mapa real en el simulador** (Fase B): repetir la batería de pruebas del banco pero con geometría
   real, antes de tocar la navegación en el robot.
3. **Navegación real** (Fase C): mapa guardado + AMCL + Nav2 **re-tuneado**, y la web en modo
   **observación real**.

Detalle y decisiones abiertas en el [plan de la Capa 1](plan-capa1-mapa-real.md).

## 9. Checklist de migración

Lista de verificación práctica, en orden. No pases de bloque hasta tenerlo en verde.

**A · Hardware y arranque**
- [ ] RPLIDAR conectado y **girando**; `/scan` a ~10 Hz, frame `laser`.
- [ ] I2C responde: encoder `0x08`, IMU `0x68`, servos `0x40/0x41` (`i2cdetect -y 1`).
- [ ] Batería cargada; **ESC armado** (neutro) y ruedas libres.
- [ ] Robot en el **suelo**, espacio despejado, `estop.sh` a mano.
- [ ] `bringupSLAM.sh` levanta todo; el chequeo de la web dice **PREPARADO**.

**B · Odometría (validar antes de confiar)**
- [ ] `ekf_node` publica `/odometry/filtered`.
- [ ] En **reposo**: deriva ≈ 0 (quieto 6 s).
- [ ] Empujando ~1 m a mano: la odometría **avanza coherente** (no en el banco: ruedas al aire).
- [ ] Giro a mano: el **yaw** responde en el sentido correcto.

**C · TF / frames**
- [ ] Árbol completo `map → odom → base_link → laser` (`ros2 run tf2_tools view_frames`).
- [ ] El láser en frame `laser` (montaje **180°** aplicado por TF).

**D · SLAM y mapa (Fase A)**
- [ ] Arrancar **alineado con una pared** y **quieto ~2 s** (calibra giróscopo, fija el (0,0) recto).
- [ ] `cartographer` publica `/map`; el mapa **crece coherente** al conducir (no se dobla → si se
      dobla, baja velocidad / revisa EKF).
- [ ] **⏱ auto-checkpoint ON** al empezar; ante un derrape → **⤾ volver al checkpoint**.
- [ ] Al terminar: `save_map.sh piso_real` → `.pgm` + `.yaml` + `.pbstream`.
- [ ] **Limpiar el `.pgm`** (fugas del láser, muebles movidos, cerrar puertas no deseadas).

**E · Mapa real en el simulador (Fase B)**
- [ ] Cargar el `.pgm` en el banco (decisión B1 raycast-rejilla vs B2 vectorizar).
- [ ] Re-etiquetar **zonas** (cocina/baño/…).
- [ ] Repetir las **pruebas 1–8** del banco sobre la geometría real.

**F · Localización real (Fase C)**
- [ ] `map_server` carga el mapa **limpio**.
- [ ] **AMCL** converge; dar `📌 pista` si arranca disperso.
- [ ] Al conducir, **σ baja** (badge verde) y `map→odom` corrige la deriva.

**G · Nav2 re-tuneado a real**
- [ ] `footprint`/`robot_radius` reales del coche.
- [ ] **Inflado** ajustado al **ruido real** del láser (probablemente distinto del banco).
- [ ] Velocidades y **radio de giro** reales; `allow_reversing` + **dwell del ESC** al invertir.
- [ ] `collision_monitor` con **IR/US reales** (en el banco el láser 360° los hacía redundantes).

**H · Web (observación real)**
- [ ] Modo real: **ocultar** controles de sim (dibujar mapa, `▧ obstáculo`, `🌀 deriva`, `📍 real`).
- [ ] Visibles: `/scan`, `/map`, partículas/`/amcl_pose`, `/plan`, coche, destino, `📌 pista`.
- [ ] Estado de **sensores reales** (batería, IR/US crudos, ESC, encoders).

**I · Seguridad (transversal)**
- [ ] Primera navegación autónoma a **velocidad baja** y con supervisión presencial.
- [ ] `estop.sh` probado y accesible.
- [ ] Deadman del mando operativo (soltar = frena; sin conexión = frena).

---

### En una frase
El banco valida el **cerebro** (software, lógica, Nav2, web) en un mundo ideal; el mundo real añade el
**cuerpo** (sensores ruidosos, motor con inercia, física) y quita la red de seguridad (ground-truth,
sin colisiones). La migración consiste en **cambiar los sentidos y los músculos sin tocar el cerebro**,
y luego re-calibrar el cerebro a lo que de verdad siente el cuerpo.
