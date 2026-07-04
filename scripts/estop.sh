#!/bin/bash
# E-STOP Robocar: mata el nodo de control y fuerza el ESC a NEUTRO (93.6).
# Uso: bash ~/estop.sh
# v2: escribe los registros del PCA9685 en crudo (sin ServoKit) para NO
#     resetear el chip: reinicializarlo glitchea la senal y un ESC armado
#     puede dispararse (incidente jul 2026).
# La unica parada 100% fiable sigue siendo el interruptor fisico del ESC.

pkill -INT -f car_control_node 2>/dev/null
sleep 0.3
pkill -9 -f car_control_node 2>/dev/null

/home/lab/robocar/.venv/bin/python - <<'PYEOF'
import time
from smbus2 import SMBus

PCA = 0x41          # direccion real del PCA9685 en Robocar
NEUTRO = 313        # 93.6 grados = 1530us a 50Hz -> 1530/4.883 = 313 counts

def set_ch(bus, ch, counts):
    base = 0x06 + 4 * ch                    # LEDn_ON_L
    bus.write_byte_data(PCA, base, 0)       # ON = 0
    bus.write_byte_data(PCA, base + 1, 0)
    bus.write_byte_data(PCA, base + 2, counts & 0xFF)   # OFF = counts
    bus.write_byte_data(PCA, base + 3, counts >> 8)

with SMBus(1) as bus:
    for _ in range(3):
        for ch in (0, 1):
            set_ch(bus, ch, NEUTRO)
        time.sleep(0.2)
print("E-STOP OK: neutro (93.6) escrito en crudo x3, sin reset del chip")
PYEOF
