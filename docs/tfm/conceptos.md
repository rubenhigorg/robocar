# Documentos conceptuales

Explicaciones visuales de los fundamentos del robot. Cada documento se abre como **página completa** (diseño propio, con modo claro/oscuro).

## De cero: nodos, topics, TF y Nav2

Recorrido desde el principio por los conceptos base de ROS2 aplicados al robocar: **nodos**, **publicar/suscribir**, **mensajes y tipos**, **frames**, **TF** (con el árbol del robot y el bug real de `base_footprint`) y cómo encaja **Nav2**. Para reconstruir el mapa mental sin dar nada por supuesto.

[Abrir documento](de-cero-nodos-tf-nav2.md){ .md-button .md-button--primary }

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
