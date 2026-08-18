#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Calibra tan_max del modelo de direccion contra la IMU EN SUELO.
# Conduce con direccion a tope (angular.z=STEER) y compara el yaw_rate real
# (IMU gyro z) con la velocidad de rueda: tan_max = |yaw_rate|*L/(|v|*frac).
import time, statistics, rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist, TwistStamped

L = 0.175
MAXANG = 0.4
STEER = 0.4       # a tope (frac=1)
FWD = 0.2
SECS = 4.5

class Calib(Node):
    def __init__(self):
        super().__init__('calib_tan')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.wz = None; self.v = None
        self.create_subscription(Imu, '/imu', self.icb, 30)
        self.create_subscription(TwistStamped, '/wheel_speed', self.wcb, 10)
        self.samples = []

    def icb(self, m): self.wz = m.angular_velocity.z
    def wcb(self, m): self.v = m.twist.linear.x

    def run(self):
        t0 = time.time()
        while (self.wz is None or self.v is None) and time.time()-t0 < 5:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.wz is None or self.v is None:
            print('sin /imu o /wheel_speed'); return
        frac = STEER / MAXANG
        t1 = time.time()
        while time.time()-t1 < SECS:
            t = Twist(); t.linear.x = FWD; t.angular.z = STEER; self.pub.publish(t)
            rclpy.spin_once(self, timeout_sec=0.0); time.sleep(0.04)
            if time.time()-t1 > 1.2 and abs(self.v) > 0.1 and abs(self.wz) > 0.08:
                self.samples.append(abs(self.wz) * L / (abs(self.v) * frac))
        for _ in range(6):
            self.pub.publish(Twist()); time.sleep(0.05)
        if self.samples:
            self.samples.sort()
            med = statistics.median(self.samples)
            print('muestras=%d  tan_max CALIBRADO (mediana)=%.3f   (actual 0.233)'
                  % (len(self.samples), med), flush=True)
            print('=> R_min = L/tan_max = %.2f m ;  angulo rueda a tope = %.1f deg'
                  % (L/med, __import__('math').degrees(__import__('math').atan(med))), flush=True)
        else:
            print('sin muestras utiles (no giro / no se movio)', flush=True)

def main():
    rclpy.init(); n = Calib()
    try: n.run()
    except KeyboardInterrupt: n.pub.publish(Twist())
    n.destroy_node(); rclpy.shutdown()

main()
