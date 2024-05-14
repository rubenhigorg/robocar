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

IMPORTANTE 2: Para que funcione node-red (desde 0):
```
npm install -g --unsafe-perm node-red rclnodejs cron
cd /home/lab/edu_nodered_ros2_plugin
npm install -g .
```
IMPORTANTE 3: Para generar los mensajes custom, necesitamos entrar en root (sudo su) y ejecutar los siguientes comandos desde el directorio /usr/lib/node_modules/rclnodejs/scripts:
```
source /opt/ros/iron/setup.sh
source /home/ros2/robocar/src/install/setup.sh
npm run generate-messages


Debemos hacer source de los paquetes de ros2 que tenemos:
```
source /home/lab/robocar/src/install/setup.sh
```
