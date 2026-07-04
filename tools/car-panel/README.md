# Panel de control web del Robocar

Web **propia, ligera y sin dependencias** (vanilla JS, sin CDNs ni librerías): habla el
protocolo JSON de `rosbridge` directamente por WebSocket. Se sirve desde la propia Pi.

- **Vista cenital** del coche a escala real (geometría del URDF): puntos del LIDAR
  (`/scan`), haces de los ultrasonidos, anillos de distancia y zoom (0.6–8 m).
- **IMU**: sparklines de aceleración y giro en vivo.
- **Ultrasonidos**: distancias + alarma de parada de emergencia.
- **Energía**: tensiones y corriente.
- **Topics**: frescura de cada fuente de datos.

Está pensada para crecer con el TFM: aquí se añadirán el **mapa** de Cartographer,
los **goals de Nav2** (clic en el mapa) y el **chat LLM** de la Capa 3.

## Instalación (una vez, en la Pi)

```bash
sudo apt install ros-humble-rosbridge-suite
```

## Arranque

```bash
bash ~/robocar/tools/car-panel/launch-panel.sh
```

Abrir **http://robocar.local:8080** en cualquier navegador de la red.

## Arquitectura

```
Pi ── nodos ROS2 (imu, us, energy, scan, TF)
   ├─ rosbridge_server ── ws JSON :9090 ◄── app.js (suscripciones directas)
   └─ http.server :8080 ── index.html + app.js + style.css
```

La geometría del coche está duplicada en `app.js` (constante `CAR`) — si cambia el
URDF, actualizarla a mano (consciente: evita parsear xacro en el navegador).
