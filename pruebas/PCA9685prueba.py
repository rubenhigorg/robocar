from adafruit_servokit import ServoKit
from time import sleep

kit = ServoKit(channels=16)
servo = 0
while True:
    a = input('enter:-')
    kit.servo[0].angle = int(a)



    