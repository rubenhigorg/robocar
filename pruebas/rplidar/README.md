# Pruebas RPLIDAR

Este directorio contiene pruebas funcionales del Slamtec RPLIDAR C1 fuera de ROS2.

## Objetivo

Validar, en este orden:

1. Que el sistema detecta el lidar como puerto serie.
2. Que el SDK oficial compila correctamente.
3. Que podemos leer datos reales desde consola.
4. Que podamos visualizarlos en una interfaz web local.

## Estructura

- `build_sdk.sh`: compila el SDK oficial si está presente.
- `test_console.sh`: ejecuta una prueba mínima por consola con el binario oficial.
- `Makefile`: compila `rplidar_stream`, una utilidad C++ propia basada en el SDK.
- `rplidar_stream.cpp`: lee scans con el SDK y emite frames JSON.
- `web_viewer.py`: visualización web local en tiempo real.
- `rplidar_check.cpp`: prueba funcional automatizable del sensor.
- `run_sensor_test.sh`: wrapper para lanzar la prueba funcional.

## Ubicación esperada del SDK

Por simplicidad, este directorio asume que el SDK oficial se encuentra en:

`pruebas/rplidar/rplidar_sdk`

Se puede clonar aquí:

```bash
cd /home/hub/robocar/pruebas/rplidar
git clone https://github.com/Slamtec/rplidar_sdk.git
```

## Compilación

```bash
cd /home/hub/robocar/pruebas/rplidar
./build_sdk.sh
```

## Prueba por consola

Primero localiza el puerto serie:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Después ejecuta:

```bash
cd /home/hub/robocar/pruebas/rplidar
./test_console.sh /dev/ttyUSB0
```

El RPLIDAR C1 usa `460800` baudios. El script lo usa por defecto:

```bash
./test_console.sh /dev/ttyUSB0 460800
```

## Visualizador web

Compila primero el puente basado en el SDK:

```bash
cd /home/hub/robocar/pruebas/rplidar
make
```

Arranca la interfaz, sin dependencias Python externas:

```bash
python3 web_viewer.py --serial /dev/ttyUSB0 --baudrate 460800
```

Abre en el navegador:

```bash
http://localhost:5001
```

## Notas

- En Linux puede haber problemas de permisos sobre `/dev/ttyUSB*`.
- Si el puerto existe pero no abre, revisar permisos o reglas `udev`.
- La web abre el puerto serie mientras haya un navegador conectado. Cierra la pagina antes de lanzar otra prueba que use `/dev/ttyUSB0`.

## Prueba funcional del sensor

La prueba funcional comprueba:

1. Conexion serie.
2. Lectura de device info.
3. Health status.
4. Modos de escaneo.
5. Captura de frames.
6. Puntos validos por frame.
7. Cobertura angular.
8. Ratio de puntos validos.

Ejecuta:

```bash
cd /home/hub/robocar/pruebas/rplidar
./run_sensor_test.sh /dev/ttyUSB0
```

El resultado esperado acaba en:

```text
RESULT: OK
```
