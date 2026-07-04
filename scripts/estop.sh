#!/bin/bash
# E-STOP Robocar: mata el nodo de control y fuerza el ESC a reposo.
# Uso: bash ~/estop.sh   (o desde el repo: bash scripts/estop.sh)
# Nota: la unica parada 100% fiable es el interruptor fisico del ESC.

pkill -INT -f car_control_node 2>/dev/null
sleep 0.3
pkill -9 -f car_control_node 2>/dev/null

/home/lab/robocar/.venv/bin/python - <<'PYEOF'
from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels=16)
for i in range(3):
    kit.servo[0].angle = 91.8
    kit.servo[1].angle = 91.8
    time.sleep(0.2)
print("E-STOP OK: throttle a reposo (91.8) escrito 3 veces")
PYEOF
