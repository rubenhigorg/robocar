# Capa de Interfaz Natural: LLM + MCP

[← Volver al TFM](README.md)

La capa **LLM + MCP** es el elemento que convierte a **Robocar** en un sistema controlable mediante lenguaje natural. Su función no es sustituir a ROS2, Nav2 ni a la lógica de movimiento, sino actuar como una **capa de planificación de alto nivel** capaz de interpretar la intención del usuario y traducirla en llamadas estructuradas a herramientas robóticas.

!!! info "Aportación principal del TFM"
    Esta capa es la contribución más novedosa del proyecto porque desacopla tres problemas normalmente mezclados: **comprensión del lenguaje**, **orquestación de acciones** y **ejecución robótica**. El resultado es una arquitectura más modular, portable y extensible.

## 1. LLMs y uso de herramientas (*tool use*)

Los **Large Language Models (LLMs)** son redes neuronales entrenadas con corpus masivos de texto para aprender regularidades lingüísticas, semánticas y estructurales. Los modelos actuales se basan en la arquitectura **Transformer** introducida por **Vaswani et al. (2017)**, cuyo mecanismo central es la **atención multi-cabeza** (*multi-head attention*).

Esta arquitectura permite:

- modelar dependencias de largo alcance en secuencias de texto
- mantener contexto conversacional
- generalizar a tareas no vistas explícitamente durante el entrenamiento
- combinar comprensión, generación y planificación simbólica ligera

Entre los modelos más representativos se encuentran:

| Modelo | Familia | Observación |
|---|---|---|
| **GPT-4** | OpenAI | Muy extendido en asistentes con uso de herramientas |
| **Claude** | Anthropic | Fuerte integración con razonamiento y protocolos de herramientas |
| **Gemini** | Google | Integración multimodal y ecosistema Google |
| **Llama 3** | Meta | Opción abierta para despliegues locales o híbridos |

Más allá de la generación de texto, los LLMs modernos muestran capacidades emergentes de:

- **razonamiento** sobre objetivos y restricciones
- **planificación de tareas** en varios pasos
- **comprensión contextual** de instrucciones ambiguas o incompletas
- **selección de acciones** a partir de descripciones en lenguaje natural

### Uso de herramientas y *function calling*

El salto clave para robótica no es que el modelo "hable", sino que pueda **usar herramientas externas de forma estructurada**. En lugar de limitarse a responder texto libre, el LLM puede:

1. decidir qué función necesita
2. emitir una llamada estructurada con parámetros
3. recibir la respuesta de esa herramienta
4. continuar razonando con el nuevo estado del sistema

En la práctica, esto convierte al LLM en un **agente software**. Su papel no es controlar directamente los actuadores a bajo nivel, sino **descomponer la intención del usuario** en una secuencia de acciones concretas y observables.

```text
Usuario: "Ve a la cocina"
LLM:
  1. interpreta que el objetivo es navegación semántica
  2. comprueba qué herramienta debe usar
  3. emite navigate_to(place="cocina")
  4. espera el resultado
  5. responde al usuario con el estado final
```

!!! note "Rol del LLM en este proyecto"
    En este TFM el LLM actúa como **planificador de alto nivel**. La ejecución física sigue dependiendo de ROS2 y Nav2. Esto reduce riesgo y mantiene la lógica de movimiento en componentes deterministas y auditables.

## 2. Embodied AI: LLMs en robótica

La **Embodied AI** estudia sistemas inteligentes integrados en agentes físicos que **perciben** el entorno y **actúan** sobre él. En este contexto, los LLMs aportan una interfaz semántica potente, pero deben conectarse con mecanismos que garanticen viabilidad física, percepción situada y ejecución segura.

Trabajos relevantes en esta línea incluyen:

| Trabajo | Idea principal | Relevancia para el TFM |
|---|---|---|
| **SayCan** (Ahn et al., 2022) | Combina la relevancia semántica del LLM con funciones de valor que estiman viabilidad física | Muestra que no basta con entender la orden; hay que ejecutar acciones realmente posibles |
| **RT-2** (Zitkovich et al., 2023) | Modelo visión-lenguaje-acción de extremo a extremo que genera comandos de control | Representa el enfoque más integrado entre percepción y acción |
| **LM-Nav** (Shah et al., 2023) | Descompone instrucciones de navegación en términos semánticos anclados al entorno | Muy cercano al problema de navegación natural abordado aquí |
| **Inner Monologue** (Huang et al., 2022) | Usa razonamiento interno explícito para planificación robótica | Refuerza la idea del LLM como capa deliberativa |
| **Code as Policies** (Liang et al., 2023) | Genera código que actúa como política robótica | Demuestra que el LLM puede sintetizar comportamientos estructurados, no sólo texto |

### Enfoque adoptado en este TFM

Frente a soluciones extremo a extremo o altamente dependientes de grandes recursos de cómputo, este trabajo adopta una estrategia **más pragmática y eficiente**:

- el **LLM** se usa como planificador semántico de alto nivel
- el **MCP Server** expone capacidades robóticas como herramientas estándar
- **ROS2/Nav2** mantienen la ejecución real de la navegación
- la lógica de lenguaje queda desacoplada de la lógica de movimiento

Esto aporta tres ventajas directas:

1. **modularidad**: cada capa puede evolucionar sin rediseñar el resto
2. **eficiencia computacional**: no se requiere un modelo gigantesco controlando la robótica en tiempo real
3. **extensibilidad**: añadir nuevas capacidades implica ampliar herramientas, no rehacer todo el sistema

!!! tip "Decisión de diseño"
    El objetivo no es construir un robot gobernado enteramente por un LLM, sino una **interfaz natural robusta** sobre una pila robótica clásica y fiable.

## 3. Model Context Protocol (MCP)

El **Model Context Protocol (MCP)** es un estándar abierto publicado por **Anthropic en noviembre de 2024** para conectar aplicaciones basadas en LLM con servidores externos que exponen contexto y capacidades de acción.

Su valor principal es que evita integraciones ad-hoc entre cada modelo y cada herramienta. En lugar de definir un acoplamiento específico para un único proveedor, MCP establece una interfaz común entre el modelo y los sistemas externos.

### Roles de la arquitectura MCP

| Rol | Función |
|---|---|
| **Host** | Aplicación que gestiona el LLM y la interfaz con el usuario |
| **MCP Client** | Componente embebido en el host que se comunica con uno o varios servidores MCP |
| **MCP Server** | Servicio que expone herramientas, recursos y *prompts* al LLM |

### Primitivas fundamentales

| Primitiva | Descripción | Ejemplo en Robocar |
|---|---|---|
| **Tools** | Funciones invocables por el LLM con parámetros estructurados | `navigate_to("cocina")`, `stop_navigation()` |
| **Resources** | Fuentes de datos disponibles para el modelo | estado del robot, lista de lugares conocidos |
| **Prompts** | Plantillas o instrucciones reutilizables | prompt del asistente para navegación segura |

### Canales de comunicación

MCP contempla dos mecanismos principales de transporte:

- **stdio**: apropiado cuando el servidor se ejecuta como proceso local
- **HTTP + SSE** (*Server-Sent Events*): apropiado para servicios remotos o distribuidos

### Relevancia de MCP en este TFM

El uso de MCP tiene dos implicaciones especialmente importantes:

1. **Desacoplamiento estándar entre LLM y robot**. El servidor MCP puede ampliarse o modificarse sin reescribir el LLM ni alterar la base ROS2.
2. **Portabilidad entre modelos**. Al tratarse de un estándar abierto compatible con ecosistemas de **Claude, GPT-4, Gemini** y potencialmente modelos abiertos, la arquitectura no queda atada a un único proveedor.

!!! info "Por qué MCP encaja bien en robótica"
    En una plataforma robótica real interesa separar claramente la **inteligencia deliberativa** de la **ejecución física**. MCP proporciona una frontera técnica limpia entre ambas capas.

## 4. Arquitectura LLM—MCP—ROS2

La arquitectura propuesta conecta lenguaje natural, herramientas estándar y navegación autónoma mediante una cadena de responsabilidad bien definida.

### Flujo de información extremo a extremo

```text
Usuario
  │
  │  1. "Ve a la cocina"
  ▼
LLM (razonamiento + selección de herramientas)
  │
  │  2. navigate_to("cocina")
  ▼
MCP Server
  │
  │  3. Traducción a operación ROS2
  ▼
ROS2 / Nav2
  │
  │  4. Planificación y ejecución física
  ▼
Robot móvil
  │
  │  5. Resultado / éxito / fallo / cancelación
  ▼
MCP Server
  │
  │  6. Respuesta estructurada
  ▼
LLM
  │
  │  7. Respuesta natural al usuario
  ▼
Usuario
```

### Secuencia funcional

1. **El usuario** envía una orden en lenguaje natural, por ejemplo: *"Ve a la cocina"*.
2. **El LLM** interpreta la intención, decide qué herramienta usar y en qué orden.
3. **El MCP Server** actúa como pasarela y convierte cada llamada en una operación de ROS2: publicación en tópico, invocación de servicio o, en el caso de navegación, envío de una **acción**.
4. **Nav2** recibe la meta, calcula la ruta y ejecuta la navegación de forma autónoma.
5. **Nav2** comunica el estado de finalización al MCP Server.
6. **El MCP Server** devuelve al LLM un resultado estructurado con éxito, error o cancelación.
7. **El LLM** genera la respuesta final para el usuario en lenguaje natural.

### Propiedades arquitectónicas

| Propiedad | Implicación práctica |
|---|---|
| **Separación de responsabilidades** | Lenguaje, protocolo y control robótico evolucionan de forma independiente |
| **Intercambiabilidad del modelo** | Es posible sustituir Claude por GPT o por un Llama 3 local sin rediseñar ROS2 |
| **Extensibilidad de herramientas** | Se pueden añadir nuevas acciones robóticas al MCP Server sin tocar Nav2 |
| **Observabilidad** | Cada llamada de herramienta deja una traza explícita de qué se pidió y qué devolvió el robot |
| **Sincronía controlada** | El host puede esperar al resultado de la acción antes de responder al usuario |

### Integración con ROS2 Actions

Aunque el servidor MCP puede mapear herramientas a **topics**, **services** o **actions**, la navegación punto a punto encaja especialmente bien con el patrón **ROS2 Action** (`rclpy` action client/server):

- el objetivo de navegación se envía como una meta formal
- el sistema puede recibir **feedback** durante la ejecución
- la llamada permanece activa hasta **éxito**, **fallo** o **cancelación**
- el resultado se devuelve al MCP Server, que lo retransmite al LLM

Esto permite que la conversación quede alineada con el estado real del robot. El asistente no responde "he llegado" hasta que el navegador lo confirme.

!!! note "Punto clave de robustez"
    La sincronía no la impone el LLM, sino el mecanismo de acciones de ROS2. El LLM solicita; ROS2 ejecuta y confirma.

## 5. Herramientas del MCP Server

El servidor MCP del proyecto expone cuatro herramientas iniciales, suficientes para cubrir el caso de uso principal de navegación semántica en interiores.

| Herramienta | Descripción | Parámetros |
|---|---|---|
| `navigate_to()` | Navega al lugar indicado | nombre del lugar |
| `get_current_location()` | Devuelve la posición actual del robot | — |
| `list_known_places()` | Lista los lugares etiquetados disponibles | — |
| `stop_navigation()` | Detiene la navegación en curso | — |

### Rol de cada herramienta

#### `navigate_to()`
Convierte un destino semántico como *"cocina"* o *"salón"* en una meta de navegación entendible por ROS2/Nav2. Es la herramienta principal del sistema y la que conecta lenguaje natural con movimiento físico.

#### `get_current_location()`
Permite consultar dónde está el robot desde una perspectiva semántica o referenciada al mapa. Es útil para diálogo, depuración y validación contextual antes de lanzar movimientos.

#### `list_known_places()`
Expone al modelo y al usuario el conjunto de ubicaciones disponibles. Reduce ambigüedad y permite respuestas del tipo: *"Conozco cocina, laboratorio y entrada"*.

#### `stop_navigation()`
Cancela la navegación activa. Es importante tanto para control manual como para seguridad operacional y recuperación ante cambios de intención del usuario.

```text
Ejemplo de interacción:
- Usuario: "¿Qué lugares conoces?"
- LLM: list_known_places()
- MCP Server: ["cocina", "salón", "entrada"]
- LLM: "Puedo ir a cocina, salón o entrada"
```

!!! tip "Extensión futura"
    Esta interfaz puede crecer con herramientas como `get_battery_status()`, `dock()`, `describe_surroundings()` o `navigate_through(waypoints)` sin alterar la estructura general del sistema.

## 6. Diferenciación respecto a trabajos previos

La propuesta se diferencia de gran parte de la literatura y de muchas demos experimentales en tres aspectos clave:

1. **Uso de MCP como protocolo estándar**. Frente a soluciones ad-hoc basadas en *prompts*, cadenas manuales o APIs propietarias directas, aquí la interfaz entre modelo y robot se formaliza mediante un estándar abierto.
2. **Despliegue sobre hardware real y de bajo coste**. La solución se implementa sobre **Raspberry Pi 4** y **RPLidar C1**, apoyándose en software completamente abierto: **ROS2**, **Cartographer**, **Nav2** y **FastMCP**.
3. **Continuidad sobre una plataforma previa consolidada**. El TFM no parte de cero: aprovecha la base física, electrónica y software desarrollada en los dos TFG anteriores, lo que permite centrar la innovación en la integración semántica y no en rehacer la plataforma.

### Lectura de conjunto

En términos prácticos, el valor del sistema no está sólo en que un LLM "entienda" órdenes, sino en que lo haga sobre una arquitectura:

- **estándar** en la frontera de herramientas
- **modular** en su diseño interno
- **transferible** entre proveedores de LLM
- **compatible** con robótica real basada en ROS2

!!! info "Resumen"
    La capa **LLM + MCP** convierte a Robocar en un sistema navegable por lenguaje natural sin sacrificar modularidad, trazabilidad ni control sobre la ejecución física. Es, por tanto, la pieza que une la semántica del usuario con la autonomía operativa del robot.
