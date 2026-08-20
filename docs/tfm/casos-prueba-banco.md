# Casos de prueba del banco (simulador)

Batería de pruebas manuales para el **panel web** del banco (`:8080/trayectorias.html`, modo
**MAPA·Nav2** salvo que se diga). Cada caso indica **qué hacer** y **qué debería pasar** (para saber
si pasa o falla). Los marcados con 🔥 son los que más suelen destapar problemas.

> **Cómo reportar un fallo:** el caso + lo que viste. Si puedes, abre la consola del navegador
> (**F12 → Console**) y copia lo que salga en rojo.

---

## Referencia rápida de la interfaz

- **Modo:** `▦ MAPA·Nav2` (por defecto) / `◦ RUTA` (script antiguo, aparte).
- **Fila MAPA:** `🏠 Plantas…` · `▭ habitación` · `─ pared` · `▧ obstáculo` · `◎ destino` ·
  `🏷️ área` · `📍 real` · `📌 pista` · `↶` (deshacer) · `limpiar` · `▦ Enviar mapa`.
- **Fila Nav2:** `▶ Ir a destino` · `■ Parar` · `▨ no-go`.
- **Fila Localiz.:** `🌍 global` · `◦ partículas` · `🌀 deriva`.
- **Fila Zonas:** `[sala ▾]` · `▶ Ir a sala` · `🗑`.
- **Otros:** `ⓘ nodos` (grafo de nodos) · `⚙ Nav2` (config, la interfaz del LLM) · zoom · leyenda.

---

## 1 · Navegación básica y robustez

| Test | Acción | Esperado |
|---|---|---|
| Destino simple | Carga una planta → `◎ destino` en zona despejada → `▶ Ir a destino` | Ruta morada, conduce, "DESTINO ALCANZADO" |
| 🔥 Limpiar y renavegar | Navega → **limpiar** → dibuja otro mapa → nuevo destino | Robot al origen, mapa/zonas borrados, **el nuevo destino se alcanza** |
| 🔥 Destino imposible | `◎ destino` **sobre pared/mueble** o fuera del mapa | "No pudo llegar: inalcanzable…" (no se cuelga) |
| Parar a media ruta | `▶ Ir` → `■ Parar` a mitad | El robot se detiene, ruta cancelada |
| Ver no-go | Toggle `▨ no-go` | Aparece/desaparece el inflado rojo alrededor de las paredes |

## 2 · Marcha atrás y giro

| Test | Acción | Esperado |
|---|---|---|
| 🔥 Destino detrás | Destino **justo detrás** del robot | Retrocede para llegar (no da una vuelta enorme) |
| Desactivar reversa | `⚙ Nav2` → Marcha atrás **OFF** → destino detrás | Reinicia Nav2 ~15 s, luego solo va de frente (arco grande) |
| Puerta estrecha | Tabique con hueco ~0.6 m → destino al otro lado | La cruza |

## 3 · Config / velocidad adaptativa (`⚙ Nav2`)

| Test | Acción | Esperado |
|---|---|---|
| Velocidad | Sube **velocidad** → navega | Va más rápido en rectas |
| 🔥 Frenar en curvas | **frenar_en_curvas** alto + destino con curva | Baja en la curva, acelera en recto |
| Tolerancia | **tolerancia_objetivo** grande vs pequeña | Con grande llega antes / más fácil |
| Reinicio vs caliente | Cambia velocidad (caliente) vs marcha_atrás (reinicia) | Los "🔄" avisan de reinicio; el resto se aplica al instante |

## 4 · Obstáculos dinámicos

| Test | Acción | Esperado |
|---|---|---|
| 🔥 Obstáculo en la ruta | Carga mapa → `▶ Ir` → **mientras navega**, pinta `▧ obstáculo` en el camino | Nav2 **replanifica** rodeándolo |
| Obstáculo NO en /map | Pinta obstáculo → mira el `/map` (gris) | El láser lo ve, pero **no está en el gris** (canal aparte) |

## 5 · Zonas (áreas) + "ir a sala"

| Test | Acción | Esperado |
|---|---|---|
| Etiquetar | `🏷️ área` → rectángulo → nombre "cocina" | Zona translúcida con etiqueta |
| Ir a sala | `[cocina ▾]` → `▶ Ir a sala` | Va al **centro** de la zona |
| 🔥 Persistencia | Etiqueta zonas → **recarga (F5)** | El mapa **y sus zonas vuelven solos** (bundle en disco) |
| Borrar zona | Elige zona → `🗑` | Desaparece |
| 🔥 Limpiar borra zonas | **limpiar** | El mapa **y las zonas** se borran juntos |

## 6 · Localización (AMCL)

| Test | Acción | Esperado |
|---|---|---|
| Estado localizado | Carga mapa | Badge **◉ LOCALIZADO** (verde), partículas apiñadas en el robot |
| 🔥 Pista | `🌍 global` (se dispersan) → `📌 pista` clic donde está + arrastra rumbo | Partículas **saltan** a la pista, badge verde |
| 🔥 Deriva + AMCL corrige | `🌀 deriva` ON → manda un destino | **Llega igual de bien** (AMCL corrige la deriva) |
| Ver corrección | `🌀 deriva` ON + observa `map→odom` recolocando | La corrección se ve a saltos |
| Mapa quieto | Navega en modo normal | El **mapa NO se mueve** (histéresis de Tmo) |
| Ocultar partículas | `◦ partículas` | Se ocultan / muestran |

*(Para conducir a mano en los tests de localización: joystick en `:8080/mando.html`.)*

## 7 · Modos e independencia

| Test | Acción | Esperado |
|---|---|---|
| RUTA vs MAPA | `◦ RUTA` → dibuja waypoints → `▶ Enviar ruta` | El script antiguo los sigue (reactivo) |
| 🔥 Independencia | Trabaja en MAPA, cambia a RUTA y vuelve | No se mezclan (capas separadas) |
| Botón nodos | `ⓘ nodos` → pincha un nodo | Ficha con lenguaje, integración, pub/sub y para qué |

## 8 · Stress / casos raros (los que más destapan)

- 🔥 **Planta compleja con muebles** → destinos en habitaciones distintas (pasillos, esquinas):
  ¿alguna queda inaccesible?
- 🔥 **Zoom + arrastre** durante la navegación: ¿se descuadra algo?
- 🔥 **Recargar a media navegación**: ¿recupera el estado? ¿vuelve el mapa?
- 🔥 **Dos pestañas del panel** a la vez: ¿se pelean? (cada una es un cliente rosbridge; ojo con el throttle).
- **Destino muy pegado a una esquina** (0.2 m de dos paredes).
- **Enviar un mapa nuevo con el robot desplazado** (no en el origen): ¿el mapa cuadra?
- **Sin conexión**: apaga rosbridge o desconecta wifi → ¿el badge pasa a "desconectado" y se
  recupera al volver?

---

## Notas conocidas (comportamiento esperado, no bugs)
- El banco **engaña en localización**: la odometría es perfecta salvo que actives `🌀 deriva`
  (ver [Localización y AMCL](localizacion-amcl.md)).
- La **localización global desde cero** es el caso difícil: puede no converger sin mucho movimiento;
  usa `📌 pista` (método fiable).
- Cambiar el mapa **re-localiza AMCL** solo (tras el arreglo del *map-lock*).
