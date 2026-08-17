#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fase 4 - navegacion reactiva: va a un OBJETIVO (go-to-goal absoluto) y ESQUIVA
# obstaculos con prioridad; al despejarse, se re-apunta al objetivo -> vuelve a
# la trayectoria. Es el patron global(waypoint)+local(evitacion) de Nav2, minimal.
#
# Objetivo por defecto: goal_dist metros RECTO desde la pose inicial. Cuando un
# ultrasonido delantero ve algo cerca, la capa de evitacion sobreescribe el mando
# (gira al lado libre / frena); si no, manda el go-to-goal.
import math, rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from messages_pkg.msg import Distance

FAR = 300.0

def yaw_of(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))

class GotoAvoid(Node):
    def __init__(self):
        super().__init__('goto_avoid')
        self.declare_parameter('goal_dist', 2.0)     # m recto desde el inicio
        self.declare_parameter('drive_speed', 0.20)
        self.declare_parameter('max_angular', 0.4)
        self.declare_parameter('kp_heading', 1.5)
        self.declare_parameter('goal_tol', 0.20)
        self.declare_parameter('slow_cm', 70.0)      # obstaculo -> esquivar
        self.declare_parameter('stop_cm', 33.0)      # critico
        self.declare_parameter('side_cm', 25.0)
        self.declare_parameter('max_run_time', 40.0)

        self.pose = None; self.goal = None; self.start = None
        self.c = self.l = self.r = FAR
        self.t_start = None
        self.done = False
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odometry/filtered', self.ocb, 20)
        self.create_subscription(Distance, '/ultrasound_data', self.dcb, 10)
        self.timer = self.create_timer(1/15.0, self.loop)
        self._n = 0
        self.get_logger().info('goto_avoid listo (esperando odometria)')

    def ocb(self, m):
        p = m.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_of(p.orientation))
        if self.goal is None:
            x, y, yaw = self.pose
            gd = self.get_parameter('goal_dist').value
            self.start = (x, y)
            self.goal = (x + gd*math.cos(yaw), y + gd*math.sin(yaw))
            self.t_start = self.get_clock().now()
            self.get_logger().info('OBJETIVO a %.1f m recto: (%.2f, %.2f)' % (gd, self.goal[0], self.goal[1]))

    def dcb(self, m):
        cl = lambda d: FAR if (d is None or d < 2.0) else d
        self.c, self.l, self.r = cl(m.center_distance), cl(m.left_distance), cl(m.right_distance)

    def loop(self):
        if self.pose is None or self.goal is None or self.done:
            return
        el = (self.get_clock().now() - self.t_start).nanoseconds/1e9
        if el > self.get_parameter('max_run_time').value:
            self._finish('timeout'); return
        x, y, yaw = self.pose
        gx, gy = self.goal
        dist = math.hypot(gx-x, gy-y)
        if dist < self.get_parameter('goal_tol').value:
            self._finish('OBJETIVO alcanzado'); return

        drive = self.get_parameter('drive_speed').value
        maxw = self.get_parameter('max_angular').value
        slow = self.get_parameter('slow_cm').value
        stop = self.get_parameter('stop_cm').value
        side = self.get_parameter('side_cm').value

        # --- go-to-goal (trayectoria) ---
        err = wrap(math.atan2(gy-y, gx-x) - yaw)
        w_nav = max(-maxw, min(maxw, self.get_parameter('kp_heading').value*err))

        # --- evitacion (prioridad si hay obstaculo) ---
        if self.c <= stop or (self.l < side and self.r < side and self.c < slow):
            if self.l < side and self.r < side:
                v, w, mode = 0.0, 0.0, 'STOP-encajonado'
            else:
                w = maxw if self.l > self.r else -maxw
                v, w, mode = 0.0, w, 'GIRA-critico'
        elif self.c <= slow:
            w = maxw if self.l > self.r else -maxw
            v, w, mode = drive*0.6, w, 'ESQUIVA'
        else:
            v, w, mode = drive, w_nav, 'NAV'    # sin obstaculo -> sigue la trayectoria

        t = Twist(); t.linear.x = float(v); t.angular.z = float(w); self.pub.publish(t)
        self._n = (self._n+1) % 8   # ~2 Hz
        if self._n == 0:
            self.get_logger().info('%-14s dist_goal=%.2f err=%+.0f | c=%.0f l=%.0f r=%.0f (v=%.2f w=%+.2f)'
                                   % (mode, dist, math.degrees(err), self.c, self.l, self.r, v, w))

    def _finish(self, why):
        self.done = True
        for _ in range(4):
            self.pub.publish(Twist())
        sx, sy = self.start
        self.get_logger().info('FIN (%s). Desviacion final del inicio=%.2f m'
                               % (why, math.hypot(self.pose[0]-sx, self.pose[1]-sy)))

def main():
    rclpy.init(); n = GotoAvoid()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.pub.publish(Twist()); n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
