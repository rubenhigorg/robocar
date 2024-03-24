from adafruit_servokit import ServoKit
from time import sleep
import sys

print(sys.executable)
print("hola")   
kit = ServoKit(channels=16)
while True:
    a = input('enter:-')
    a = float(a)*1.8
    kit.servo[0].angle = a
    kit.servo[1].angle = a
    #kit.servo[2].angle = int(a)




    