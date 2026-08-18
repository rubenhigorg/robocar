#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Odometria por ANGULO DE DIRECCION (modelo bicicleta Ackermann).
# De la velocidad de rueda v (/wheel_speed, con signo) y la direccion delta
# (derivada de /cmd_vel angular.z) calcula la velocidad angular de guiñada:
#     yaw_rate = v * tan(delta) / L
# y la publica como TwistWithCovarianceStamped (solo vyaw) en /steer_yaw_cov,
# para que el EKF la fusione como twist1 compitiendo con la IMU. La COVARIANZA
# (param yaw_variance) es el PESO -> define el perfil de odometria:
#   - suelo normal: yaw_variance ALTA (poco peso; manda la IMU).
#   - banco / IMU no fiable: yaw_variance BAJA (manda la direccion; gira aunque
#     la IMU este plana porque el robot no se mueve de verdad).
#
# Calibracion: tan_max = tan(delta a tope) = L / R_min. CALIBRADO contra la IMU
# en suelo (calib_tan.py, dir a tope, tan_max=|yaw_rate_IMU|*L/|v|): tan_max=0.188
# -> R_min ~0.93 m, angulo de rueda a tope ~10.6 deg.
import math, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped, TwistWithCovarianceStamped

class SteerYaw(Node):
    def __init__(self):
        super().__init__('steer_yaw_node')
        self.declare_parameter('wheelbase', 0.175)       # L (m)
        self.declare_parameter('tan_max', 0.188)         # tan(delta_max)=L/R_min. Calibrado vs IMU en suelo: R_min~0.93 m
        self.declare_parameter('max_angular', 0.4)       # angular.z a tope de giro (= car_control)
        self.declare_parameter('yaw_variance', 0.5)      # covarianza vyaw = PESO (bajo=mas peso)
        self.declare_parameter('rate_hz', 30.0)
        self.declare_parameter('frame_id', 'base_link')

        self.L = float(self.get_parameter('wheelbase').value)
        self.tan_max = float(self.get_parameter('tan_max').value)
        self.max_ang = float(self.get_parameter('max_angular').value)
        self.frame_id = self.get_parameter('frame_id').value

        self.v = 0.0        # velocidad de rueda (m/s, con signo)
        self.ang = 0.0      # angular.z comandado
        self._n = 0

        self.create_subscription(TwistStamped, '/wheel_speed', self.wcb, 10)
        self.create_subscription(Twist, '/cmd_vel', self.ccb, 10)
        self.pub = self.create_publisher(TwistWithCovarianceStamped, '/steer_yaw_cov', 10)
        rate = float(self.get_parameter('rate_hz').value)
        self.create_timer(1.0 / rate, self.tick)
        self.get_logger().info('steer_yaw_node listo (L=%.3f, tan_max=%.3f, yaw_var=%.3f)'
                               % (self.L, self.tan_max, self.get_parameter('yaw_variance').value))

    def wcb(self, m):
        self.v = m.twist.linear.x

    def ccb(self, m):
        self.ang = m.angular.z

    def tick(self):
        frac = max(-1.0, min(1.0, self.ang / self.max_ang)) if self.max_ang else 0.0
        tan_delta = self.tan_max * frac
        yaw_rate = self.v * tan_delta / self.L        # modelo bicicleta

        msg = TwistWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.twist.twist.angular.z = yaw_rate
        var = float(self.get_parameter('yaw_variance').value)   # leer en vivo (perfil ajustable)
        cov = [0.0] * 36
        cov[35] = var        # varianza de vyaw (indice 5,5)
        msg.twist.covariance = cov
        self.pub.publish(msg)

        self._n = (self._n + 1) % 30    # ~1 Hz
        if self._n == 0:
            self.get_logger().info('v=%+.2f ang=%+.2f -> yaw_rate=%+.3f rad/s (var=%.3f)'
                                   % (self.v, self.ang, yaw_rate, var))

def main():
    rclpy.init(); n = SteerYaw()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
