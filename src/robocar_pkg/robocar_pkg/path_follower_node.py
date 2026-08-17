#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
path_follower_node — recorrido predefinido para el robocar (Ackermann) con giros
en 3 puntos (marcha atras) para poder cerrar esquinas cerradas (p.ej. cuadrado 1 m).

Enfoque RELATIVO y robusto al hardware:
  - LADOS: avanzar 'side' metros en recto, midiendo la DISTANCIA recorrida por
    odometria (siempre hacia delante -> el encoder sin sentido es fiable aqui),
    con correccion suave de rumbo por yaw (IMU).
  - ESQUINAS: girar 'corner_angle' grados mediante un VAIVEN adelante/atras
    (giro en 3+ puntos): adelante girando hacia el lado, marcha atras
    contra-girando; ambas fases hacen avanzar el YAW en el mismo sentido. Se
    mide por el cambio de YAW (IMU), NO por posicion -> inmune a que el encoder
    no distinga el sentido en la reversa. Cada fase se limita a 'kturn_seg_max'
    metros para caber en poco espacio.

Kinematica clave (car_control mapea angular.z -> angulo de direccion):
  yaw_rate = (v/L)*tan(delta).  Para seguir girando a la IZQUIERDA:
    - adelante (v>0): direccion IZQUIERDA (angular.z>0)
    - marcha atras (v<0): direccion DERECHA (angular.z<0)  [contra-giro]

Seguridad: solo actua en modo AUTONOMO; arranque por servicio ~start; ~stop
aborta; al terminar/abortar/cerrar -> /cmd_vel a cero; timeout global.
"""
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class PathFollowerNode(Node):
    def __init__(self):
        super().__init__('path_follower_node')
        # --- geometria del recorrido ---
        self.declare_parameter('side', 1.0)              # lado del cuadrado (m)
        self.declare_parameter('sides', 4)               # nº de lados (4 = cuadrado)
        self.declare_parameter('corner_angle_deg', 90.0) # giro en cada esquina
        self.declare_parameter('direction', 'ccw')       # 'ccw' (izq) o 'cw' (der)
        self.declare_parameter('loops', 1)
        # --- velocidades (crawl fiable ~0.20; por debajo el ESC se cala) ---
        self.declare_parameter('fwd_speed', 0.20)        # m/s adelante (recto y fase F del giro)
        self.declare_parameter('rev_speed', 0.20)        # m/s marcha atras (fase R del giro)
        self.declare_parameter('max_angular', 0.4)       # tope direccion (rad/s), = car_control
        self.declare_parameter('heading_kp', 1.6)        # correccion de rumbo en recto
        # --- tolerancias / limites ---
        self.declare_parameter('dist_tol', 0.05)         # m para dar por hecho un lado
        self.declare_parameter('yaw_tol_deg', 6.0)       # grados para dar por hecho un giro
        self.declare_parameter('kturn_seg_max', 0.35)    # m max por fase del vaiven
        self.declare_parameter('phase_time_max', 3.5)    # s max por fase (anti-atasco)
        self.declare_parameter('max_run_time', 120.0)    # s corte de seguridad global
        self.declare_parameter('rate_hz', 15.0)
        self.declare_parameter('odom_topic', '/odometry/filtered')
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('autostart', False)

        self.max_ang = self.get_parameter('max_angular').value
        self.turn_sign = 1.0 if self.get_parameter('direction').value == 'ccw' else -1.0
        odom_topic = self.get_parameter('odom_topic').value
        cmd_topic = self.get_parameter('cmd_topic').value

        # --- estado ---
        self.pose = None
        self.state = 'IDLE'          # IDLE | STRAIGHT | TURN | DONE
        self.start_pose = None
        self.side_start = None       # (x,y) al empezar el lado actual
        self.target_heading = 0.0    # rumbo objetivo del lado actual
        self.legs_done = 0
        self.total_legs = 0
        # sub-estado del giro
        self.turn_target = 0.0
        self.turn_phase = 'FWD'
        self.phase_start = None      # (x,y)
        self.phase_t0 = None
        self.corners_done = 0
        self.t_start = None
        self._log_div = 0

        self.sub = self.create_subscription(Odometry, odom_topic, self.odom_cb, 20)
        self.pub = self.create_publisher(Twist, cmd_topic, 10)
        self.create_service(Trigger, '~/start', self.on_start)
        self.create_service(Trigger, '~/stop', self.on_stop)
        rate = self.get_parameter('rate_hz').value
        self.timer = self.create_timer(1.0 / rate, self.control_loop)

        self.get_logger().info(
            'path_follower (giros 3 puntos) listo. Arranca con: '
            'ros2 service call /path_follower_node/start std_srvs/srv/Trigger')

    # ---------------- callbacks ----------------
    def odom_cb(self, msg):
        p = msg.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_from_quat(p.orientation))
        if self.state == 'IDLE' and self.get_parameter('autostart').value and self.start_pose is None:
            self._begin()

    def on_start(self, req, resp):
        if self.pose is None:
            resp.success = False
            resp.message = 'Sin odometria (/odometry/filtered). Lanza el EKF.'
            return resp
        self._begin()
        resp.success = True
        resp.message = 'Recorrido iniciado.'
        return resp

    def on_stop(self, req, resp):
        self._halt('parada solicitada')
        resp.success = True
        resp.message = 'Detenido.'
        return resp

    # ---------------- helpers ----------------
    def _publish(self, lin, ang):
        t = Twist()
        t.linear.x = float(lin)
        t.angular.z = float(ang)
        self.pub.publish(t)

    def _now(self):
        return self.get_clock().now()

    def _begin(self):
        x, y, yaw = self.pose
        self.start_pose = (x, y, yaw)
        self.side_start = (x, y)
        self.target_heading = yaw
        self.legs_done = 0
        self.total_legs = int(self.get_parameter('sides').value) * int(self.get_parameter('loops').value)
        self.corners_done = 0
        self.t_start = self._now()
        self.state = 'STRAIGHT'
        self.get_logger().info(
            'ARRANQUE en (%.2f, %.2f, %.0f deg). %d lados de %.2f m, giro %.0f deg %s.'
            % (x, y, math.degrees(yaw), self.total_legs,
               self.get_parameter('side').value,
               self.get_parameter('corner_angle_deg').value,
               self.get_parameter('direction').value))

    def _halt(self, reason):
        if self.state in ('STRAIGHT', 'TURN'):
            if self.start_pose is not None and self.pose is not None:
                sx, sy, _ = self.start_pose
                err = math.hypot(self.pose[0] - sx, self.pose[1] - sy)
                self.get_logger().info('STOP (%s). Error de cierre = %.3f m.' % (reason, err))
            else:
                self.get_logger().info('STOP (%s).' % reason)
        self.state = 'DONE'
        for _ in range(3):
            self._publish(0.0, 0.0)

    def _timeout(self):
        el = (self._now() - self.t_start).nanoseconds / 1e9
        return el > self.get_parameter('max_run_time').value

    # ---------------- control ----------------
    def control_loop(self):
        if self.state in ('IDLE', 'DONE') or self.pose is None:
            return
        if self._timeout():
            self._halt('timeout')
            return
        if self.state == 'STRAIGHT':
            self._straight()
        elif self.state == 'TURN':
            self._turn()

    def _straight(self):
        x, y, yaw = self.pose
        sx, sy = self.side_start
        d = math.hypot(x - sx, y - sy)
        side = self.get_parameter('side').value
        if d >= side - self.get_parameter('dist_tol').value:
            self.legs_done += 1
            self.get_logger().info('Lado %d/%d hecho (%.2f m).' % (self.legs_done, self.total_legs, d))
            if self.legs_done >= self.total_legs:
                self._halt('completado')
                return
            # iniciar giro en la esquina
            ca = math.radians(self.get_parameter('corner_angle_deg').value)
            self.turn_target = wrap(self.target_heading + self.turn_sign * ca)
            self.turn_phase = 'FWD'
            self.phase_start = (x, y)
            self.phase_t0 = self._now()
            self.state = 'TURN'
            self.get_logger().info('Esquina %d: girando %.0f deg...'
                                   % (self.corners_done + 1, math.degrees(self.turn_sign * ca)))
            return
        # avanzar recto manteniendo rumbo
        err = wrap(self.target_heading - yaw)
        ang = max(-self.max_ang, min(self.max_ang, self.get_parameter('heading_kp').value * err))
        self._publish(self.get_parameter('fwd_speed').value, ang)
        self._trace('RECTO', d, err)

    def _turn(self):
        x, y, yaw = self.pose
        rem = wrap(self.turn_target - yaw)                 # yaw que falta (con signo)
        if abs(rem) < math.radians(self.get_parameter('yaw_tol_deg').value):
            # giro terminado
            self.corners_done += 1
            self.target_heading = self.turn_target
            self.side_start = (x, y)
            self.state = 'STRAIGHT'
            self._publish(0.0, 0.0)
            self.get_logger().info('Esquina %d completada (yaw ok).' % self.corners_done)
            return
        # ¿cambiar de fase? (por distancia o por tiempo)
        pd = math.hypot(x - self.phase_start[0], y - self.phase_start[1])
        pt = (self._now() - self.phase_t0).nanoseconds / 1e9
        if pd > self.get_parameter('kturn_seg_max').value or pt > self.get_parameter('phase_time_max').value:
            self.turn_phase = 'REV' if self.turn_phase == 'FWD' else 'FWD'
            self.phase_start = (x, y)
            self.phase_t0 = self._now()
        # aplicar la fase: ambas hacen avanzar el yaw en turn_sign
        if self.turn_phase == 'FWD':
            ang = self.turn_sign * self.max_ang           # direccion hacia el giro
            v = self.get_parameter('fwd_speed').value
        else:  # REV: contra-direccion, marcha atras -> mismo sentido de giro
            ang = -self.turn_sign * self.max_ang
            v = -self.get_parameter('rev_speed').value
        self._publish(v, ang)
        self._trace('GIRO-' + self.turn_phase, pd, rem)

    def _trace(self, tag, d, err):
        self._log_div = (self._log_div + 1) % max(1, int(self.get_parameter('rate_hz').value / 2))
        if self._log_div == 0:
            self.get_logger().info('%s  d=%.2f  yaw_err/rem=%+.0f deg' % (tag, d, math.degrees(err)))


def main(args=None):
    rclpy.init(args=args)
    node = PathFollowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node._halt('cierre')
        except Exception:
            pass
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
