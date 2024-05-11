from adafruit_servokit import ServoKit
from time import sleep
import sys

print(sys.executable)
print("hola")   
kit = ServoKit(channels=16)
while True:
    a = input('enter:-')
    #a = float(a)*1.8
    #kit.servo[0].angle = a
    #kit.servo[1].angle = a
    kit.servo[8].angle = int(a)
    kit.servo[7].angle = int(a)
    kit.servo[6].angle = int(a)
    kit.servo[5].angle = int(a)
    kit.servo[4].angle = int(a)
    kit.servo[3].angle = int(a)
    kit.servo[2].angle = int(a)
    kit.servo[1].angle = int(a)
    kit.servo[0].angle = int(a)
    




    