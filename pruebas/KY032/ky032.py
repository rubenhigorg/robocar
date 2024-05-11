#---------------------------------------------------
# K032 obstacle Avoidance sensor 
# VCC -------------------- 5v (Pin 2) 
# GND -------------------- GND(Pin 6)
# SIG -------------------- GPIO 21 or Pin 40 (using Board command)
# En --------------------- N/a
#
#---------------------------------------------------

import RPi.GPIO as gpio 
import time

gpio.setwarnings(False)
# using the Board command so pin number used to declared
gpio.setmode(gpio.BCM)
# Any GPIO can be used. I used 40 since it is easy to find.
gpio.setup(6,gpio.IN)


try:
# An inifinite loop with 500msec delay between every iteration    
    while True:
        x=gpio.input(6)
        if x==1:
            print("no obstacle")
            time.sleep(0.5)
        elif x==0:
            print("Obstacle detected")
            time.sleep(0.5)
# This is Keyboard interrupt with breaks the loop by pressing CTRL + C 
except KeyboardInterrupt:
    gpio.cleanup()
    print("Halt")