# robocar

Proyecto fin de grado. En este repositorio se van a subir todos los fuentes necesarios para el robot.

Instalar dependencias de python: 

```
# Solo para crear el .venv
python3 -m venv .venv

# Si ya lo tenemos: 
source .venv/bin/activate
python3 -m pip install -r requirements.txt

```

## Build ROS2 Packages: 

en el directorio raíz del repositorio: 
```
colcon build 
source install/setup.sh
```


IMPORTANTE: Para ejecutar el nodo del joystick, ejecutar el comando 
```
ros2 launch teleop_twist_joy teleop-launch.py
```
Por defecto utiliza un mando de la ps3. Mirar readme.md del paquete teleop_twist_joy para más información.
