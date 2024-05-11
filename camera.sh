#!/bin/bash
while true; do
    fswebcam -d /dev/video0 -r 320x240 --no-banner /home/lab/robocar/image.jpg
    sleep 1
done