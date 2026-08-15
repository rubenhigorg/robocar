# Documentos conceptuales

Explicaciones visuales de los fundamentos del robot. Cada documento se abre como **página completa** (diseño propio, con modo claro/oscuro).

## Odometría, SLAM y navegación

Cómo se combinan las tres piezas para llevar el robot a un destino, y cómo se relacionan sobre el árbol TF `map → odom → base_link`.

[Abrir documento](odometria-slam-navegacion.html){ .md-button .md-button--primary target="_blank" }

## Construir el mapa y esquivar obstáculos

Dos capítulos: cómo se **construye un mapa** (SLAM) y cómo el robot **evita obstáculos que no están en él** (costmaps de Nav2).

[Abrir documento](construir-mapa-y-obstaculos.html){ .md-button .md-button--primary target="_blank" }

## Ángulo de dirección y deslizamiento en la odometría

Estudio teórico: qué aporta el **modelo de bicicleta** (usar el ángulo de dirección) a la odometría, y cómo la degradan los **deslizamientos** — el patinaje de las ruedas motrices al arrancar y el derrape lateral en curva. Incluye la geometría del modelo, las ecuaciones y una comparativa de robustez por fuente.

[Abrir documento](estudio-direccion-deslizamiento.html){ .md-button .md-button--primary target="_blank" }
