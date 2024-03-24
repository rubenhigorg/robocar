from adafruit_servokit import ServoKit
from time import sleep

# Inicializa el controlador PCA9685 con 16 canales
kit = ServoKit(channels=16)

# Función para inicializar el motor
def initialize_motor(channel):
    # Envia una señal de 1000us (1ms) para inicializar el motor
    kit.servo[channel].set_pulse_width_range(1000, 2000)
    kit.servo[channel].angle = 0
    sleep(1)

# Función para calibrar el ESC
def calibrate_esc(channel):
    # Envia una señal máxima
    kit.servo[channel].angle = 180
    sleep(1)
    # Envia una señal mínima
    kit.servo[channel].angle = 0
    sleep(1)

# Función para controlar el motor
def control_motor(channel, speed):
    # Convierte la velocidad (0-100) a un ángulo (0-180)
    angle = speed * 1.8
    # Envia la señal al motor
    kit.servo[channel].angle = angle

# Inicializa y calibra los motores

initialize_motor(0)
initialize_motor(1)
calibrate_esc(0)
calibrate_esc(1)

# Demostración de control de motores
for speed in range(50, 10, -1):  # De 50 a 0 (hacia atrás)
    control_motor(0, speed)
    control_motor(1, speed)
    print("speed: ")
    print(speed)
    sleep(0.1)

#for speed in range(51, 101):  # De 51 a 100 (hacia adelante)
 #   control_motor(0, speed)
  #  control_motor(1, speed)
   # sleep(0.1)

control_motor(0,50)
control_motor(1,50)