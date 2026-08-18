#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fase 5.1 - seguidor de una LISTA DE WAYPOINTS con evitacion de obstaculos.
# Generaliza goto_avoid: recibe la trayectoria por topic (/plan_waypoints,
# PoseArray) con waypoints RELATIVOS a la pose de arranque (x=adelante, y=izq).
# Los recorre con go-to-goal absoluto + evitacion reactiva con prioridad, y
# publica estado (/trajectory_nav/status) para la web.
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
        self.declare_parameter('kp_heading', 1.5)
        self.declare_parameter('goal_tol', 0.20)
        self.declare_parameter('slow_cm', 70.0)
        self.declare_parameter('stop_cm', 33.0)
        self.declare_parameter('side_cm', 25.0)
        self.declare_parameter('avoid_enabled', True)
        self.declare_parameter('max_run_time', 120.0)

        self.pose = None
        self.c = self.l = self.r = FAR
        self.wps = []          # waypoints en odom [(x,y),...]
        self.idx = 0
        self.state = 'IDLE'    # IDLE | RUN | DONE
        self.start = None
        self.t_start = None
        self._n = 0

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.stpub = self.create_publisher(String, '/trajectory_nav/status', 10)
        self.create_subscription(Odometry, '/odometry/filtered', self.ocb, 20)
        self.create_subscription(Distance, '/ultrasound_data', self.dcb, 10)
        self.create_subscription(PoseArray, '/plan_waypoints', self.wcb, 10)
        self.create_timer(1/15.0, self.loop)
        self.get_logger().info('trajectory_nav listo. Publica waypoints (relativos) en /plan_waypoints (PoseArray).')

    def ocb(self, m):
        p = m.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_of(p.orientation))

    def dcb(self, m):
        cl = lambda d: FAR if (d is None or d < 2.0) else d
        self.c, self.l, self.r = cl(m.center_distance), cl(m.left_distance), cl(m.right_distance)

    def wcb(self, msg):
        # PoseArray con waypoints RELATIVOS a la pose actual (x adelante, y izq)
        if self.pose is None:
            self.get_logger().warn('Sin odometria todavia; ignoro waypoints.')
            return
        if len(msg.poses) == 0:
            self._stop('lista vacia -> parar'); return
        x0, y0, yaw0 = self.pose
        c, s = math.cos(yaw0), math.sin(yaw0)
        self.wps = []
        for p in msg.poses:
            rx, ry = p.position.x, p.position.y
            self.wps.append((x0 + rx*c - ry*s, y0 + rx*s + ry*c))
        self.start = (x0, y0)
        self.idx = 0
        self.state = 'RUN'
        self.t_start = self.get_clock().now()
        self.get_logger().info('TRAYECTORIA recibida: %d waypoints.' % len(self.wps))
        self._status()

    def _stop(self, why):
        if self.state == 'RUN':
            self.get_logger().info('STOP (%s).' % why)
        self.state = 'DONE'
        for _ in range(3):
            self.pub.publish(Twist())
        self._status()

    def _status(self):
        m = String()
        m.data = 'state=%s wp=%d/%d' % (self.state, self.idx, len(self.wps))
        self.stpub.publish(m)

    def loop(self):
        if self.state != 'RUN' or self.pose is None:
            return
        el = (self.get_clock().now() - self.t_start).nanoseconds/1e9
        if el > self.get_parameter('max_run_time').value:
            self._stop('timeout'); return
        x, y, yaw = self.pose
        gx, gy = self.wps[self.idx]
        dist = math.hypot(gx-x, gy-y)
        if dist < self.get_parameter('goal_tol').value:
            self.idx += 1
            if self.idx >= len(self.wps):
                sx, sy = self.start
                self.get_logger().info('TRAYECTORIA COMPLETA. Desviacion del inicio=%.2f m'
                                       % math.hypot(x-sx, y-sy))
                self._stop('completada'); return
            self.get_logger().info('Waypoint %d/%d alcanzado.' % (self.idx, len(self.wps)))
            self._status(); return

        drive = self.get_parameter('drive_speed').value
        maxw = self.get_parameter('max_angular').value
        slow = self.get_parameter('slow_cm').value
        stop = self.get_parameter('stop_cm').value
        side = self.get_parameter('side_cm').value
        avoid = self.get_parameter('avoid_enabled').value

        err = wrap(math.atan2(gy-y, gx-x) - yaw)
        w_nav = max(-maxw, min(maxw, self.get_parameter('kp_heading').value*err))

        mode = 'NAV'; v, w = drive, w_nav
        if avoid and (self.c <= stop or (self.l < side and self.r < side and self.c < slow)):
            if self.l < side and self.r < side:
                v, w, mode = 0.0, 0.0, 'STOP-encaj'
            else:
                w = maxw if self.l > self.r else -maxw
                v, w, mode = 0.0, w, 'GIRA-crit'
        elif avoid and self.c <= slow:
            w = maxw if self.l > self.r else -maxw
            v, w, mode = drive*0.6, w, 'ESQUIVA'

        t = Twist(); t.linear.x = float(v); t.angular.z = float(w); self.pub.publish(t)
        self._n = (self._n+1) % 8
        if self._n == 0:
            self.get_logger().info('%-10s wp %d/%d d=%.2f err=%+.0f c=%.0f (v=%.2f w=%+.2f)'
                                   % (mode, self.idx+1, len(self.wps), dist, math.degrees(err), self.c, v, w))
            self._status()

def main():
    rclpy.init(); n = TrajectoryNav()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.pub.publish(Twist()); n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
