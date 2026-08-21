# Documentos conceptuales

Explicaciones visuales de los fundamentos del robot. Cada documento se abre como **página completa** (diseño propio, con modo claro/oscuro).

## De cero: nodos, topics, TF y Nav2

Recorrido desde el principio por los conceptos base de ROS2 aplicados al robocar: **nodos**, **publicar/suscribir**, **mensajes y tipos**, **frames**, **TF** (con el árbol del robot y el bug real de `base_footprint`) y cómo encaja **Nav2**. Para reconstruir el mapa mental sin dar nada por supuesto.

[Abrir documento](de-cero-nodos-tf-nav2.md){ .md-button .md-button--primary }

## Control de la navegación por el LLM (Capa 3)

Catálogo de todo lo que un LLM podrá controlar sobre Nav2: **velocidad adaptativa** (rápido en rectas, lento en curvas/obstáculos, límites por zona) y **condicionar la ruta** (pasar por puntos, zonas prohibidas/lentas, pegado a pared vs centro, orientación…). Con el estado de cada palanca y la arquitectura de control (`/nav_config` + objetivos + máscaras).

[Abrir documento](control-navegacion-llm.md){ .md-button .md-button--primary }

## Plan de optimización del banco

Auditoría de los **nodos** que corren en el banco (lenguaje, integración colcon, qué publica/escucha cada uno) + **perfilado de CPU/RAM** real en la Pi4, y un **plan priorizado por ROI** para hacerlo más eficiente y ordenado. Incluye el veredicto razonado sobre **si pasar nodos a C++** mejora (spoiler: casi nunca es la palanca).

[Abrir documento](optimizacion-banco.md){ .md-button .md-button--primary }

## Localización: pose inicial, deriva y por qué AMCL es imprescindible

Los **dos** problemas que resuelve la localización: **dónde estoy al arrancar** (la cascada dock → última pose → pista → global) y **seguir sabiéndolo mientras me muevo** (la **deriva** que acumula la odometría y que **AMCL corrige** encajando láser+mapa). Explica las dos capas TF (`odom→base_link` + `map→odom`), por qué en el banco parece innecesario (odometría perfecta = espejismo) y por qué en el **robot real es imprescindible**.

[Abrir documento](localizacion-amcl.md){ .md-button .md-button--primary }

## Odometría, SLAM y navegación

Cómo se combinan las tres piezas para llevar el robot a un destino, y cómo se relacionan sobre el árbol TF `map → odom → base_link`.

[Abrir documento](odometria-slam-navegacion.html){ .md-button .md-button--primary target="_blank" }

## Construir el mapa y esquivar obstáculos

Dos capítulos: cómo se **construye un mapa** (SLAM) y cómo el robot **evita obstáculos que no están en él** (costmaps de Nav2).

[Abrir documento](construir-mapa-y-obstaculos.html){ .md-button .md-button--primary target="_blank" }

## Ángulo de dirección y deslizamiento en la odometría

Estudio teórico: qué aporta el **modelo de bicicleta** (usar el ángulo de dirección) a la odometría, y cómo la degradan los **deslizamientos** — el patinaje de las ruedas motrices al arrancar y el derrape lateral en curva. Incluye la geometría del modelo, las ecuaciones y una comparativa de robustez por fuente.

[Abrir documento](estudio-direccion-deslizamiento.html){ .md-button .md-button--primary target="_blank" }

## Pesos de sensores y perfiles de odometría

Estudio de diseño: en la fusión (EKF) el **peso de cada sensor es su covarianza**. Ajustándola por sensor —y por eje— se definen **perfiles de odometría** adaptados a cada ambiente (sala, pasillo, espacio abierto, suelo resbaladizo). Incluye el mecanismo de `robot_localization`, la fuerza de cada sensor por entorno y recetas de pesos.

[Abrir documento](perfiles-odometria.html){ .md-button .md-button--primary target="_blank" }

## Mapa de nodos ROS2

Qué nodos corren en el robocar, qué **publica y consume** cada uno y cómo se encadenan (sensores → odometría → SLAM → control → web), con el árbol TF. Incluye un **grafo interactivo** (todos los nodos, arrastrables, con ficha de cada uno y sus topics de publicación/suscripción).

[Abrir documento](nodos-ros2.html){ .md-button .md-button--primary target="_blank" }
[Grafo interactivo](nodos-ros2-grafo.html){ .md-button target="_blank" }

## Casos de prueba del banco (simulador)

Batería de **pruebas manuales** del panel web: navegación, marcha atrás, config/velocidad adaptativa, obstáculos dinámicos, zonas, **localización (AMCL)** y casos de estrés. Cada caso indica qué hacer y qué debería pasar, para saber si pasa o falla.

[Abrir documento](casos-prueba-banco.md){ .md-button .md-button--primary }

## Plan · Capa 1: mapa real y migración a la realidad

Plan en tres saltos para pasar del banco al robot real: **cartografiar el piso** con el mando (Cartographer/SLAM), **meter el mapa real en el simulador** para repetir las pruebas sobre geometría realista, y **migrar la navegación a la realidad** adaptando la web para observar al robot navegando el mapa generado. Aterrizado en lo que ya existe (RPLIDAR, `robocar_slam`, EKF), con los huecos a cubrir y las decisiones abiertas.

[Abrir documento](plan-capa1-mapa-real.md){ .md-button .md-button--primary }

## Del banco a la realidad: simulación vs mundo real

Documento de estudio de la migración **sim → real**: qué del banco se traslada tal cual, qué eran **espejismos** (láser perfecto, odometría perfecta, sin colisiones) y qué problemas nuevos aparecen con el robot físico (deriva, derrapes, ruido). El marco conceptual de la Capa 1.

[Abrir documento](del-banco-a-la-realidad.md){ .md-button .md-button--primary }
