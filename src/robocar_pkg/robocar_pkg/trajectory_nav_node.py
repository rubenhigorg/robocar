#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fase 5 - seguidor de una LISTA DE WAYPOINTS con evitacion + k-turn de reserva.
# Recibe la trayectoria por topic (/plan_waypoints, PoseArray, relativos a la pose
# de arranque). La recorre con go-to-goal absoluto (suave). Prioridades:
#   1) emergencia IR (parada inmediata)  2) evitacion ultrasonica  3) trayectoria.
# HIBRIDO: si un waypoint es INALCANZABLE arqueando (cae dentro del circulo de giro
# minimo R_min -> el go-to-goal orbitaria), hace un GIRO EN 3 PUNTOS (k-turn) para
# reorientarse hacia el; cuando queda alcanzable, vuelve a go-to-goal.
# Publica estado en /trajectory_nav/status.
import math, rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, PoseArray
from std_msgs.msg import String
from messages_pkg.msg import Distance

FAR = 300.0
def yaw_of(q): return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
def wrap(a): return math.atan2(math.sin(a), math.cos(a))

class TrajectoryNav(Node):
    def __init__(self):
        super().__init__('trajectory_nav')
        self.declare_parameter('drive_speed', 0.20)
        self.declare_parameter('max_angular', 0.4)
        # salida /cmd_vel en convencion ESTANDAR (twist): angular.z = velocidad de giro (rad/s),
        # para que sim_motion (modo twist) y Nav2 compartan la misma interpretacion. La logica
        # interna sigue en "mando de direccion normalizado"; _pub() convierte al publicar.
        self.declare_parameter('output_twist', True)
        self.declare_parameter('wheelbase', 0.175)
        self.declare_parameter('tan_max', 0.188)
        self.declare_parameter('kp_heading', 1.5)
        self.declare_parameter('goal_tol', 0.20)
        self.declare_parameter('slow_cm', 70.0)
        self.declare_parameter('stop_cm', 33.0)
        self.declare_parameter('side_cm', 25.0)
        self.declare_parameter('avoid_enabled', True)
        self.declare_parameter('emergency_enabled', True)
        self.declare_parameter('max_run_time', 120.0)
        # --- k-turn de reserva (giros cerrados) ---
        self.declare_parameter('kturn_enabled', True)
        self.declare_parameter('r_min', 0.95)            # radio de giro minimo (m) para reachability
        self.declare_parameter('kturn_fwd', 0.20)
        self.declare_parameter('kturn_rev', 0.20)
        self.declare_parameter('kturn_seg_max', 0.30)    # m por fase del vaiven
        self.declare_parameter('neutral_dwell', 0.9)     # s en neutro al invertir sentido (ESC)
        self.declare_parameter('phase_time_max', 4.5)
        self.declare_parameter('kturn_time_max', 25.0)   # s max por k-turn (anti-atasco)

        self.pose = None
        self.c = self.l = self.r = FAR
        self.emergency = False
        self.wps = []; self.idx = 0
        self.state = 'IDLE'          # IDLE | RUN | DONE
        self.start = None; self.t_start = None
        self._n = 0
        # sub-estado k-turn
        self.kturn = False
        self.turn_sign = 1.0
        self.turn_phase = 'FWD'
        self.phase_start = None; self.phase_t0 = None
        self.kturn_t0 = None
        self.last_move_dir = 0; self.neutral_until = None

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.stpub = self.create_publisher(String, '/trajectory_nav/status', 10)
        self.create_subscription(Odometry, '/odometry/filtered', self.ocb, 20)
        self.create_subscription(Distance, '/ultrasound_data', self.dcb, 10)
        self.create_subscription(PoseArray, '/plan_waypoints', self.wcb, 10)
        self.create_timer(1/15.0, self.loop)
        self.get_logger().info('trajectory_nav listo (con k-turn de reserva). Waypoints en /plan_waypoints.')

    # ---------- callbacks ----------
    def ocb(self, m):
        p = m.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_of(p.orientation))

    def dcb(self, m):
        cl = lambda d: FAR if (d is None or d < 2.0) else d
        self.c, self.l, self.r = cl(m.center_distance), cl(m.left_distance), cl(m.right_distance)
        self.emergency = (not bool(m.emergency_stop))

    def wcb(self, msg):
        if self.pose is None:
            self.get_logger().warn('Sin odometria; ignoro waypoints.'); return
        if len(msg.poses) == 0:
            self._stop('lista vacia -> parar'); return
        x0, y0, yaw0 = self.pose
        c, s = math.cos(yaw0), math.sin(yaw0)
        self.wps = [(x0 + p.position.x*c - p.position.y*s,
                     y0 + p.position.x*s + p.position.y*c) for p in msg.poses]
        self.start = (x0, y0); self.idx = 0
        self.kturn = False; self.neutral_until = None; self.last_move_dir = 0
        self.state = 'RUN'; self.t_start = self.get_clock().now()
        self.get_logger().info('TRAYECTORIA recibida: %d waypoints.' % len(self.wps))
        self._status()

    # ---------- helpers ----------
    def _pub(self, lin, ang):
        # ang llega como mando de direccion normalizado (+-max_angular = tope). Si output_twist,
        # se convierte a velocidad de giro real yaw_rate = v*tan_max*(ang/max_angular)/L, que es
        # como lo entiende sim_motion en modo twist (y Nav2). Movimiento identico al de antes.
        if self.get_parameter('output_twist').value:
            L = self.get_parameter('wheelbase').value
            tmax = self.get_parameter('tan_max').value
            maxa = self.get_parameter('max_angular').value
            ratio = (ang / maxa) if maxa > 0 else 0.0
            ang = lin * tmax * ratio / L
        t = Twist(); t.linear.x = float(lin); t.angular.z = float(ang); self.pub.publish(t)

    def _now_s(self):
        return self.get_clock().now().nanoseconds / 1e9

    def _drive(self, v, ang):
        """Publica respetando pausa en neutro al invertir el sentido (el ESC no
        reversa desde movimiento). Devuelve True si aplico el comando."""
        d = 0 if abs(v) < 1e-3 else (1 if v > 0 else -1)
        now = self._now_s()
        if d != 0 and self.last_move_dir != 0 and d != self.last_move_dir and self.neutral_until is None:
            self.neutral_until = now + self.get_parameter('neutral_dwell').value
        if self.neutral_until is not None:
            if now < self.neutral_until:
                self._pub(0.0, ang); return False
            self.neutral_until = None
        if d != 0:
            self.last_move_dir = d
        self._pub(v, ang); return True

    def reachable(self, x, y, yaw, gx, gy):
        """True si el waypoint se puede alcanzar arqueando hacia delante (esta FUERA
        del circulo de giro minimo del lado correspondiente)."""
        R = self.get_parameter('r_min').value
        hx, hy = math.cos(yaw), math.sin(yaw)
        cross = hx*(gy-y) - hy*(gx-x)          # >0 = waypoint a la izquierda
        if cross >= 0:
            cx, cy = x - R*hy, y + R*hx         # centro circulo izquierdo
        else:
            cx, cy = x + R*hy, y - R*hx         # centro circulo derecho
        return math.hypot(gx-cx, gy-cy) >= R

    def _status(self, mode=''):
        m = String(); m.data = 'state=%s wp=%d/%d%s' % (self.state, self.idx, len(self.wps),
                                                        (' '+mode) if mode else ''); self.stpub.publish(m)

    def _stop(self, why):
        if self.state == 'RUN':
            self.get_logger().info('STOP (%s).' % why)
        self.state = 'DONE'
        for _ in range(3): self._pub(0.0, 0.0)
        self._status()

    # ---------- control ----------
    def loop(self):
        if self.state != 'RUN' or self.pose is None:
            return
        if (self.get_clock().now()-self.t_start).nanoseconds/1e9 > self.get_parameter('max_run_time').value:
            self._stop('timeout'); return
        # 1) emergencia IR (siempre, maxima prioridad)
        if self.get_parameter('emergency_enabled').value and self.emergency:
            self._pub(0.0, 0.0)
            self._n = (self._n+1) % 15
            if self._n == 0: self.get_logger().warn('EMERGENCIA (IR) -> STOP'); self._status('EMERGENCIA')
            return
        x, y, yaw = self.pose
        gx, gy = self.wps[self.idx]
        dist = math.hypot(gx-x, gy-y)
        if dist < self.get_parameter('goal_tol').value:
            self.idx += 1; self.kturn = False; self.neutral_until = None
            if self.idx >= len(self.wps):
                sx, sy = self.start
                self.get_logger().info('TRAYECTORIA COMPLETA. Desviacion inicio=%.2f m' % math.hypot(x-sx, y-sy))
                self._stop('completada'); return
            self.get_logger().info('Waypoint %d/%d alcanzado.' % (self.idx, len(self.wps)))
            self._status(); return
        # 2) k-turn en curso?
        if self.kturn:
            self._do_kturn(x, y, yaw, gx, gy, dist); return
        # 3) waypoint inalcanzable arqueando -> iniciar k-turn
        if self.get_parameter('kturn_enabled').value and not self.reachable(x, y, yaw, gx, gy):
            hx, hy = math.cos(yaw), math.sin(yaw)
            cross = hx*(gy-y) - hy*(gx-x)
            self.turn_sign = 1.0 if cross >= 0 else -1.0
            self.kturn = True; self.turn_phase = 'FWD'
            self.phase_start = (x, y); self.phase_t0 = None; self.kturn_t0 = self._now_s()
            self.get_logger().info('Waypoint cerrado -> K-TURN (%s)' % ('izq' if self.turn_sign > 0 else 'der'))
            self._status('KTURN'); return
        # 4) NAV normal (go-to-goal + evitacion)
        self._nav(x, y, yaw, gx, gy, dist)

    def _nav(self, x, y, yaw, gx, gy, dist):
        drive = self.get_parameter('drive_speed').value
        maxw = self.get_parameter('max_angular').value
        slow = self.get_parameter('slow_cm').value; stop = self.get_parameter('stop_cm').value
        side = self.get_parameter('side_cm').value; avoid = self.get_parameter('avoid_enabled').value
        err = wrap(math.atan2(gy-y, gx-x) - yaw)
        w_nav = max(-maxw, min(maxw, self.get_parameter('kp_heading').value*err))
        mode = 'NAV'; v, w = drive, w_nav
        if avoid and (self.c <= stop or (self.l < side and self.r < side and self.c < slow)):
            if self.l < side and self.r < side: v, w, mode = 0.0, 0.0, 'STOP-encaj'
            else: w = maxw if self.l > self.r else -maxw; v, w, mode = 0.0, w, 'GIRA-crit'
        elif avoid and self.c <= slow:
            w = maxw if self.l > self.r else -maxw; v, w, mode = drive*0.6, w, 'ESQUIVA'
        # NAV mueve siempre hacia delante -> resetea la guardia de sentido
        self.last_move_dir = 1 if v > 0 else self.last_move_dir
        self._pub(v, w)
        self._log(mode, dist, err)

    def _do_kturn(self, x, y, yaw, gx, gy, dist):
        # fin del k-turn: el waypoint ya es alcanzable arqueando (o timeout)
        if self.reachable(x, y, yaw, gx, gy):
            self.kturn = False; self.neutral_until = None; self._pub(0.0, 0.0)
            self.get_logger().info('K-TURN completado -> NAV'); self._status('NAV')
            return
        if self._now_s() - self.kturn_t0 > self.get_parameter('kturn_time_max').value:
            self.kturn = False; self.get_logger().warn('K-TURN timeout -> NAV'); return
        pd = math.hypot(x-self.phase_start[0], y-self.phase_start[1])
        pt = (self._now_s()-self.phase_t0) if self.phase_t0 is not None else 0.0
        if pd > self.get_parameter('kturn_seg_max').value or pt > self.get_parameter('phase_time_max').value:
            self.turn_phase = 'REV' if self.turn_phase == 'FWD' else 'FWD'
            self.phase_start = (x, y); self.phase_t0 = None
        maxw = self.get_parameter('max_angular').value
        if self.turn_phase == 'FWD':
            ang = self.turn_sign*maxw; v = self.get_parameter('kturn_fwd').value
        else:
            ang = -self.turn_sign*maxw; v = -self.get_parameter('kturn_rev').value
        applied = self._drive(v, ang)
        if applied and self.phase_t0 is None: self.phase_t0 = self._now_s()
        self._log('KTURN-'+self.turn_phase, dist, wrap(math.atan2(gy-y, gx-x)-yaw))

    def _log(self, mode, dist, err):
        self._n = (self._n+1) % 8
        if self._n == 0:
            self.get_logger().info('%-11s wp %d/%d d=%.2f err=%+.0f c=%.0f'
                                   % (mode, self.idx+1, len(self.wps), dist, math.degrees(err), self.c))
            self._status(mode)

def main():
    rclpy.init(); n = TrajectoryNav()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n._pub(0.0, 0.0); n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
