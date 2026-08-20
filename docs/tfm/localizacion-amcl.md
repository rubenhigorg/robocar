# Localización: pose inicial, deriva, y por qué AMCL es imprescindible en el mundo real

Para navegar, el robot no necesita solo un **mapa** y saber **conducir**: necesita saber **dónde
está DENTRO del mapa**, en todo momento. Y eso plantea **dos preguntas distintas**:

1. **¿Dónde estoy al arrancar?** — la *pose inicial* (no se conoce: depende de dónde lo enciendas).
2. **¿Sigo sabiendo dónde estoy mientras me muevo?** — corregir la *deriva* que acumula la odometría.

**AMCL** (Adaptive Monte Carlo Localization, el filtro de partículas estándar de ROS/Nav2)
resuelve **las dos** con el mismo mecanismo: **encajar el láser contra el mapa**. La segunda —la
corrección continua— es la que hace que AMCL sea **imprescindible en el robot real**, aunque en el
banco de simulación parezca innecesaria. Este documento explica por qué.

---

## 1. El problema de la pose inicial

En la realidad, al encender, el robot **no sabe dónde está** en el mapa. AMCL lo resuelve con
**localización global**: reparte cientos de hipótesis (*partículas*) por todo el mapa; cada barrido
del láser puntúa cada partícula por lo bien que encaja con el mapa en esa pose; las malas mueren,
las buenas sobreviven. Con el robot **quieto** en un mapa poco ambiguo converge; en un mapa
**simétrico** (habitaciones/pasillos iguales) quedan varias hipótesis → hay que **moverse** para
desambiguar.

**Pero "global desde cero" NO es como se localiza un robot en la práctica.** Lo habitual es una
**cascada**, de lo más barato/fiable a lo más costoso:

| Método | Cómo | Uso real |
|---|---|---|
| **Pose de arranque conocida** | siempre enciende en un sitio fijo (base de carga / *dock*) | Lo más común (aspiradoras, reparto, AGV) |
| **Última pose conocida + verificar** | recuerda dónde estaba al apagarse y lo confirma con el 1.er barrido | Muy pragmático |
| **Pista aproximada** (RViz *2D Pose Estimate*) | un humano clica "estás ~aquí" y AMCL afina | Habitual en industria/servicio |
| **Global + auto-mover** | partículas por todo el mapa; el robot conduce hasta converger | **Último recurso** (robot "secuestrado", perdido de verdad) |

> **Conclusión práctica:** la localización global es el **caso difícil** (lenta, falla en mapas
> grandes/simétricos) y se reserva como *fallback*. La vía principal es **acotar** la pose inicial
> (dock, última conocida o pista). Lo verificamos en el banco: global se resistía, y en cuanto le
> dimos una **pista** convergió.

---

## 2. El problema de la deriva (el importante durante el trayecto)

La **odometría** es *dead-reckoning* ("cuenta de pasos"): integra velocidad y giro para estimar la
pose. Su defecto es que **acumula error y nunca lo corrige**:

- cada **patinazo** de rueda, cada giro imperfecto, cada imprecisión del **ángulo de dirección**,
  cada baldosa irregular → un pequeño error que se **suma** y no se borra.
- En un trayecto largo, la pose estimada **deriva** de la real (decenas de cm, y creciendo).

**AMCL corrige esa deriva de forma CONTINUA:** en cada barrido del láser reajusta las partículas
contra el mapa y publica la **corrección `map→odom`**. Así la pose en el mapa se mantiene **exacta
aunque la odometría derive**.

Sin esta corrección, sobre un trayecto real:
- el robot **cree** que llegó al destino, pero está desviado (la deriva acumulada);
- puede **derivar contra una pared**, porque su idea de dónde está el muro (en el mapa) ya no cuadra
  con dónde está él de verdad;
- la incertidumbre **crece sin límite** con la distancia.

---

## 3. La arquitectura: dos capas, no una

No es "odometría **o** AMCL": es **las dos a la vez**, en dos eslabones del árbol TF. Cada una aporta
lo que a la otra le falta.

| Eslabón TF | Quién lo publica | Carácter |
|---|---|---|
| `odom → base_link` | **odometría** (encoders + dirección + IMU) | **suave y rápida** (~50 Hz), pero **deriva** |
| `map → odom` | **AMCL** (láser + mapa) | **a saltos y lenta** (~pocos Hz), pero **acota la deriva** |
| `map → base_link` | la **composición** de las dos | pose real en el mapa: **exacta Y suave** |

```
        AMCL (corrige la deriva, a saltos)
   map ───────────────▶ odom ───────────────▶ base_link
                              odometría (suave, rápida, deriva)
   └──────────────── map → base_link ─────────────────┘
                 (lo que usa Nav2 para planificar y conducir)
```

**¿Por qué no usar solo AMCL?** Porque es **discreto y a saltos** (actualiza con el movimiento, a
baja frecuencia) y puntualmente puede equivocarse. El controlador necesita una pose **suave y a alta
frecuencia** para conducir liso → esa la da la **odometría**. AMCL solo le da el "empujón" cada
tanto para que no se vaya. **Lo mejor de cada uno.**

---

## 4. El espejismo del banco

En el **banco (simulación)** la odometría es **perfecta**: `sim_motion` integra con matemática
exacta, **sin patinazo ni ruido**. Como **no hay deriva que corregir**, AMCL **no aporta nada al
trayecto** — por eso "antes, sin AMCL, todo funcionaba muy bien". **Es un artefacto de la
simulación**, no una propiedad del robot real.

De hecho, la localización es **la capa donde el banco engaña más**:
- **Más fácil** de lo real: odometría perfecta, láser sin ruido.
- **Más difícil** de forma artificial: en sim el robot **atraviesa las paredes** (no hay colisión
  física) → el láser ve incoherencias → AMCL se pierde. El robot real **no puede atravesar un muro**,
  así que ese problema **desaparece** en la realidad.

---

## 5. Por qué en el mundo real es IMPRESCINDIBLE

Juntando lo anterior:

| | Solo odometría (pose inicial conocida) | Con AMCL |
|---|---|---|
| Arranque en sitio desconocido | ❌ imposible | ✅ localización global/pista |
| Trayecto corto, suelo bueno | ✅ aceptable | ✅ |
| Trayecto largo / patinazo / giros | ❌ **deriva** (llega desviado, choca) | ✅ pose **acotada**, llega exacto |
| Incertidumbre con la distancia | crece **sin límite** | **acotada** por el mapa |

**El valor de AMCL escala con:** la **longitud** del trayecto, lo **mala** que sea la odometría
(peor odometría → más valor), y la **precisión** que exijas al llegar. En un robot Ackermann real
—donde el ángulo de dirección y el patinaje degradan la odometría— es **necesario** para navegar con
fiabilidad más allá de unos pocos metros.

---

## 6. Qué validamos en el banco (y qué aprendimos)

**Funciona (verificado):**
- AMCL infiere una pose oculta con ~**5 cm** de error (test honesto: `sim_sensors` lanza el láser
  desde una pose real que AMCL no conoce).
- **La confianza sube al moverse** (la covarianza baja de σ≈0.5 a σ≈0.2) — el filtro converge.
- Visualización en la web: nube de partículas + elipse de confianza + badge LOCALIZADO.

**Limitaciones / aprendizajes:**
- La **global desde cero** es el caso duro (lenta, falla en mapas grandes/simétricos).
- **Artefactos de sim**: atravesar paredes y el teletransporte (`/set_pose`) pelean con AMCL (se
  parcheó el teletransporte publicando `/initialpose`).
- **`first_map_only`**: AMCL fija el primer mapa; cambiarlo pide reiniciarlo (deuda técnica del banco).

---

## 7. Conclusión

- **AMCL no es solo para el punto inicial.** Su trabajo principal es la **corrección continua de la
  deriva** durante todo el trayecto, y por eso en el robot real es **imprescindible**.
- En el **banco no se ve su valor** porque la odometría es perfecta; es un espejismo.
- Lo **robusto** es una **cascada**: pose conocida / última / pista como vía principal, y **global +
  auto-mover** como último recurso.

**Test que le falta al banco (para justificar AMCL aquí):** inyectar **deriva simulada** en
`sim_motion` (un error sistemático + ruido en la integración) y comparar **llegar a un destino con y
sin AMCL** — sin él, el robot llegaría **desviado**; con él, la corrección `map→odom` lo mantiene
exacto. Es la prueba que convierte el banco en un test **fiel** de localización.

---

*Ver también: [De cero: nodos, TF y Nav2](de-cero-nodos-tf-nav2.md), [Odometría, SLAM y
navegación](odometria-slam-navegacion.html), [Roadmap](roadmap.md) (Capa 1 / decisión D2).*
