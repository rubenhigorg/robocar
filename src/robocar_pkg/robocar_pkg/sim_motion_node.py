#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modelo de movimiento CINEMATICO (bicicleta Ackermann) para el banco en SIM PURO.
#
# Integra /cmd_vel y publica /odometry/filtered + TF odom->base_link, SIN depender de las
# ruedas / encoder / IMU / EKF. Es el "planta simulada": convierte el mando en pose, igual
# que haria el robot real en el suelo, pero de forma reproducible y sin hardware.
#
# Usa los MISMOS parametros que la odometria de direccion (steer_yaw_node): wheelbase,
# tan_max, max_angular -> el radio de giro minimo y el disparo del k-turn en sim COINCIDEN
# con la realidad. Asi lo que valides aqui (incl. Nav2) se traslada al suelo.
#
#   /cmd_vel (Twist) --> [integra x,y,yaw] --> /odometry/filtered (Odometry) + TF odom->base_link
#   angular.z se interpreta como el mando de direccion (satura a +-max_angular = tope de rueda),
#   tan(delta) = tan_max * clamp(angular.z/max_angular, -1, 1);  yaw_rate = v * tan(delta) / L.
#   /set_pose (PoseWithCovarianceStamped) reinicia la pose (boton "Origen" de la web).
import math, json, random, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped, PoseWithCovarianceStamped, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Bool
from tf2_ros import TransformBroadcaster


class SimMotion(Node):
    def __init__(self):
        super().__init__('sim_motion')
        self.declare_parameter('wheelbase', 0.175)     # L (m)
        self.declare_parameter('tan_max', 0.188)       # tan(delta) a tope (R_min ~ 0.93 m)
        self.declare_parameter('max_angular', 0.4)     # angular.z que satura la direccion
        self.declare_parameter('rate_hz', 50.0)
        self.declare_parameter('cmd_timeout', 0.5)     # sin /cmd_vel -> para (watchdog)
        # como interpretar angular.z de /cmd_vel:
        #   'twist'      = velocidad de giro deseada en rad/s (ESTANDAR ROS / Nav2)
        #   'steer_norm' = mando de direccion normalizado, +-max_angular = tope (trajectory_nav/car_control)
        self.declare_parameter('cmd_mode', 'steer_norm')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        # DERIVA de odometria (para el test de localizacion): la ODOMETRIA publicada se aparta de
        # la pose REAL. Sin deriva (por defecto) odom==real (banco clasico). Ajustable en caliente.
        self.declare_parameter('drift_enabled', False)
        self.declare_parameter('drift_yaw_per_m', 0.10)   # rad de error de rumbo por metro (deriva sistematica)
        self.declare_parameter('drift_dist', 0.0)         # error de escala de distancia (0.05 = +5%)
        self.declare_parameter('drift_noise', 0.0)        # ruido gaussiano por paso (rad)

        # pose ODOM (publicada, puede DERIVAR) y pose REAL (verdad del mundo, exacta)
        self.x = 0.0; self.y = 0.0; self.yaw = 0.0
        self.tx = 0.0; self.ty = 0.0; self.tyaw = 0.0
        self.v = 0.0; self.wz = 0.0
        self.last_cmd = None
        self.drift_on = self.get_parameter('drift_enabled').value   # toggle en caliente via /sim_drift (web)

        self.pub = self.create_publisher(Odometry, '/odometry/filtered', 20)   # odom (posible deriva)
        self.pub_truth = self.create_publisher(PoseStamped, '/truth_pose', 10)  # pose REAL (para sim_sensors y medir)
        # al teletransportar (reset del banco) avisamos a AMCL de la pose conocida (evita que se descoloque)
        self.pub_init = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.tfb = TransformBroadcaster(self)
        self.create_subscription(Twist, '/cmd_vel', self.ccb, 10)
        self.create_subscription(PoseWithCovarianceStamped, '/set_pose', self.rcb, 10)
        self.create_subscription(String, '/sim_truth', self.tcb, 10)   # coloca la pose REAL (test localizacion)
        self.create_subscription(Bool, '/sim_drift', self.dcb, 10)      # ON/OFF deriva desde la web

        self.dt = 1.0 / self.get_parameter('rate_hz').value
        self.create_timer(self.dt, self.tick)
        self.get_logger().info('sim_motion listo (integra /cmd_vel -> /odometry/filtered + TF odom->base_link)')

    def now_s(self):
        t = self.get_clock().now().to_msg()
        return t.sec + t.nanosec * 1e-9

    def ccb(self, m):
        self.v = m.linear.x
        L = self.get_parameter('wheelbase').value
        tmax = self.get_parameter('tan_max').value
        if self.get_parameter('cmd_mode').value == 'twist':
            # ESTANDAR ROS/Nav2: angular.z = velocidad de giro deseada (rad/s).
            # Ackermann: tan(delta) = omega*L/v, limitado por el tope de direccion.
            if abs(self.v) > 1e-3:
                tand = max(-tmax, min(tmax, m.angular.z * L / self.v))
                self.wz = self.v * tand / L
            else:
                self.wz = 0.0     # sin avance no hay giro (Ackermann no rota en el sitio)
        else:
            # 'steer_norm': angular.z normalizado, +-max_angular = tope de direccion.
            maxa = self.get_parameter('max_angular').value
            ratio = max(-1.0, min(1.0, (m.angular.z / maxa) if maxa > 0 else 0.0))
            self.wz = self.v * (tmax * ratio) / L
        self.last_cmd = self.now_s()

    def rcb(self, m):
        p = m.pose.pose; q = p.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        # reset del banco: pose CONOCIDA -> odom y real coinciden
        self.x = self.tx = p.position.x; self.y = self.ty = p.position.y
        self.yaw = self.tyaw = yaw
        self.v = 0.0; self.wz = 0.0
        self.get_logger().info('pose reiniciada a (%.2f, %.2f, %.0f deg)' % (self.x, self.y, math.degrees(self.yaw)))
        # sincroniza AMCL: en el reset la pose es CONOCIDA (map==odom en el banco) -> initialpose
        ip = PoseWithCovarianceStamped(); ip.header.frame_id = 'map'
        ip.header.stamp = self.get_clock().now().to_msg()
        ip.pose.pose.position.x = self.x; ip.pose.pose.position.y = self.y
        ip.pose.pose.orientation.z = math.sin(self.yaw/2); ip.pose.pose.orientation.w = math.cos(self.yaw/2)
        cov = [0.0]*36; cov[0] = 0.10; cov[7] = 0.10; cov[35] = 0.03; ip.pose.covariance = cov
        self.pub_init.publish(ip)

    def tcb(self, msg):
        # coloca la pose REAL sin tocar la odometria -> el robot esta "de verdad" en otro sitio
        # que AMCL no conoce (test de pose inicial desconocida). {"x":..,"y":..,"yaw":..}
        try:
            d = json.loads(msg.data)
            self.tx = float(d.get('x', 0.0)); self.ty = float(d.get('y', 0.0)); self.tyaw = float(d.get('yaw', 0.0))
            self.get_logger().info('pose REAL (oculta) fijada: (%.2f, %.2f, %.0f deg)'
                                   % (self.tx, self.ty, math.degrees(self.tyaw)))
        except Exception:
            pass

    def dcb(self, m):
        self.drift_on = bool(m.data)
        self.get_logger().info('DERIVA de odometria %s' % ('ACTIVADA' if self.drift_on else 'desactivada'))

    def tick(self):
        to = self.get_parameter('cmd_timeout').value
        if self.last_cmd is None or (self.now_s() - self.last_cmd) > to:
            self.v = 0.0; self.wz = 0.0
        # integracion Euler — pose REAL (exacta, la verdad del mundo)
        self.tx += self.v * math.cos(self.tyaw) * self.dt
        self.ty += self.v * math.sin(self.tyaw) * self.dt
        self.tyaw = math.atan2(math.sin(self.tyaw + self.wz * self.dt), math.cos(self.tyaw + self.wz * self.dt))
        # pose ODOM (lo que el robot "cree") — con DERIVA opcional respecto a la real
        if self.drift_on:
            ds = self.v * self.dt
            vs = 1.0 + self.get_parameter('drift_dist').value
            nz = self.get_parameter('drift_noise').value
            yaw_err = self.get_parameter('drift_yaw_per_m').value * abs(ds) + (random.gauss(0.0, nz) if nz > 0 else 0.0)
            self.x += self.v * vs * math.cos(self.yaw) * self.dt
            self.y += self.v * vs * math.sin(self.yaw) * self.dt
            self.yaw += self.wz * self.dt + yaw_err
        else:
            self.x += self.v * math.cos(self.yaw) * self.dt
            self.y += self.v * math.sin(self.yaw) * self.dt
            self.yaw += self.wz * self.dt
        self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        now = self.get_clock().now().to_msg()
        of = self.get_parameter('odom_frame').value
        bf = self.get_parameter('base_frame').value
        cy = math.cos(self.yaw * 0.5); sy = math.sin(self.yaw * 0.5)

        od = Odometry()
        od.header.stamp = now; od.header.frame_id = of; od.child_frame_id = bf
        od.pose.pose.position.x = self.x; od.pose.pose.position.y = self.y
        od.pose.pose.orientation.z = sy; od.pose.pose.orientation.w = cy
        od.twist.twist.linear.x = self.v; od.twist.twist.angular.z = self.wz
        for i in (0, 7, 14, 21, 28, 35):
            od.pose.covariance[i] = 0.01; od.twist.covariance[i] = 0.01
        self.pub.publish(od)

        t = TransformStamped()
        t.header.stamp = now; t.header.frame_id = of; t.child_frame_id = bf
        t.transform.translation.x = self.x; t.transform.translation.y = self.y
        t.transform.rotation.z = sy; t.transform.rotation.w = cy
        self.tfb.sendTransform(t)

        # pose REAL (verdad del mundo) en frame map: la usa sim_sensors para el laser y se mide el error
        tp = PoseStamped(); tp.header.stamp = now; tp.header.frame_id = 'map'
        tp.pose.position.x = self.tx; tp.pose.position.y = self.ty
        tp.pose.orientation.z = math.sin(self.tyaw * 0.5); tp.pose.orientation.w = math.cos(self.tyaw * 0.5)
        self.pub_truth.publish(tp)


def main():
    rclpy.init(); n = SimMotion()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
