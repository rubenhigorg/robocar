import RPi.GPIO as GPIO 
import time
GPIO.setmode (GPIO.BCM)


# amarillo
TRIG = 12
ECHO = 13

''' Los pines listos para recibir señales son: 
HC derecha (TRIG = 23, ECHO = 24)
HC frente (TRIG = 5, ECHO = 6)
HC izquierda (TRIG = 17, ECHO = 27)
*derecha e izquierda mirando hacia delante del coche como si lo condujeses
*Chequear pines físicos en  KentoDrafts/I2C_adress_table&Rpi_pin_table.docx
'''

print("Distance Measurement In Progress")
GPIO.setup (TRIG, GPIO.OUT)
GPIO.setup (ECHO, GPIO.IN)
GPIO.output (TRIG, False)
print("Waiting For Sensor To Settle")
time.sleep (2)

GPIO.output (TRIG, True) 
time.sleep(0.00001) 
GPIO.output (TRIG, False)

while GPIO.input (ECHO)==0:
    pulse_start = time.time()
while GPIO.input (ECHO)==1: 
    pulse_end = time.time()

pulse_duration = pulse_end - pulse_start
distance = pulse_duration * 17150
distance = round(distance, 2)
print(f"Distance: {distance}, cm")
GPIO.cleanup()