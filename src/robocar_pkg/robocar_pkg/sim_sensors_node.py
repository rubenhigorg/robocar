#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Simulador de sensores desde un MAPA dibujado por web (banco preparatorio).
# Recibe el mapa (/sim_map, std_msgs/String JSON de segmentos-pared, relativos a
# la pose del coche al enviarlo) y, por RAY-CASTING desde la pose actual del coche
# (/odometry/filtered), publica los sensores COMO SI el coche estuviera en ese mapa:
#   - /ultrasound_data (messages_pkg/Distance): 3 ultrasonidos delanteros (cm) + IR.
#   - /scan (sensor_msgs/LaserScan): laser virtual 360 (para visualizar / Nav2 futuro).
# Sustituye a distance_node/rplidar en modo BANCO. El coche "gira" por la odometria
# de direccion (perfil banco), asi que navega el mapa dibujado sin entorno real.
import json, math, rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import String
from messages_pkg.msg import Distance

def ray_seg(px, py, dx, dy, ax, ay, bx, by):
    """Distancia t>=0 del rayo (P, D) al segmento A-B, o None."""
    ex, ey = bx-ax, by-ay
    den = dx*ey - dy*ex
    if abs(den) < 1e-9:
        return None
    t = ((ax-px)*ey - (ay-py)*ex) / den
    u = ((ax-px)*dy - (ay-py)*dx) / den
    if t >= 0.0 and 0.0 <= u <= 1.0:
        return t
    return None

class SimSensors(Node):
    def __init__(self):
        super().__init__('sim_sensors')
        self.declare_parameter('rate_hz', 12.0)
        self.declare_parameter('n_scan', 120)            # rayos del laser virtual
        self.declare_parameter('scan_max', 4.0)          # m
        self.declare_parameter('us_max_cm', 300.0)       # alcance ultrasonidos (cm)
        self.declare_parameter('us_side_deg', 30.0)      # apertura sensores lat.
        self.declare_parameter('emergency_cm', 15.0)     # IR: objeto muy cerca
        self.declare_parameter('scan_frame', 'base_link')

        self.segs = []      # segmentos-pared en frame ODOM [(ax,ay,bx,by),...]
        self.obs = []       # obstaculos dinamicos (NO van al /map, solo al /scan)
        self.pose = None
        self.pub_us = self.create_publisher(Distance, '/ultrasound_data', 10)
        self.pub_scan = self.create_publisher(LaserScan, '/scan', 10)
        # ultrasonidos como sensor_msgs/Range (para la range_sensor_layer del costmap de Nav2).
        # (offset x,y en base_link, yaw, frame) segun el URDF: centro y +-25 grados.
        self.us_cfg = [(0.25, 0.0, 0.0, 'ultrasound_center'),
                       (0.24, 0.0525, 0.436, 'ultrasound_left'),
                       (0.24, -0.0525, -0.436, 'ultrasound_right')]
        self.pub_range = {n: self.create_publisher(Range, '/us_' + n.split('_')[1], 10)
                          for _, _, _, n in self.us_cfg}
        self.pub_ir = self.create_publisher(Range, '/ir_range', 10)   # IR de proximidad (emergencia)
        self.ir_max = 0.5
        self.create_subscription(Odometry, '/odometry/filtered', self.ocb, 20)
        self.create_subscription(String, '/sim_map', self.mcb, 10)
        self.create_subscription(String, '/sim_obstacles', self.obcb, 10)
        rate = self.get_parameter('rate_hz').value
        self.create_timer(1.0/rate, self.tick)
        self.get_logger().info('sim_sensors listo (mapa por /sim_map, publica /ultrasound_data + /scan)')

    def ocb(self, m):
        p = m.pose.pose
        q = p.orientation
        yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
        self.pose = (p.position.x, p.position.y, yaw)

    def mcb(self, msg):
        # segmentos relativos (x adelante, y izq) -> transformar a ODOM con la pose actual
        if self.pose is None:
            self.get_logger().warn('Sin odometria; ignoro mapa.'); return
        try:
            data = json.loads(msg.data)
            rel = data.get('segments', [])
        except Exception as e:
            self.get_logger().warn('mapa JSON invalido: %s' % e); return
        x0, y0, yaw0 = self.pose
        c, s = math.cos(yaw0), math.sin(yaw0)
        def tf(rx, ry):
            return (x0 + rx*c - ry*s, y0 + rx*s + ry*c)
        self.segs = []
        for seg in rel:
            ax, ay = tf(seg[0], seg[1]); bx, by = tf(seg[2], seg[3])
            self.segs.append((ax, ay, bx, by))
        self.get_logger().info('MAPA recibido: %d paredes.' % len(self.segs))

    def obcb(self, msg):
        # obstaculos dinamicos: mismo formato/transform que el mapa, pero solo afectan al /scan
        if self.pose is None:
            return
        try:
            rel = json.loads(msg.data).get('segments', [])
        except Exception:
            return
        x0, y0, yaw0 = self.pose
        c, s = math.cos(yaw0), math.sin(yaw0)
        self.obs = [(x0 + q[0]*c - q[1]*s, y0 + q[0]*s + q[1]*c,
                     x0 + q[2]*c - q[3]*s, y0 + q[2]*s + q[3]*c) for q in rel]
        self.get_logger().info('OBSTACULOS: %d' % len(self.obs))

    def cast(self, px, py, ang, maxd):
        dx, dy = math.cos(ang), math.sin(ang)
        best = maxd
        for (ax, ay, bx, by) in self.segs + self.obs:
            t = ray_seg(px, py, dx, dy, ax, ay, bx, by)
            if t is not None and t < best:
                best = t
        return best

    def tick(self):
        if self.pose is None:
            return
        x, y, yaw = self.pose
        # --- ultrasonidos: castea desde la posicion/direccion REAL de cada sensor ---
        us_max = self.get_parameter('us_max_cm').value / 100.0
        now = self.get_clock().now().to_msg()
        c, s = math.cos(yaw), math.sin(yaw)
        vals = {}
        for sx, sy, syaw, name in self.us_cfg:
            wx = x + sx*c - sy*s; wy = y + sx*s + sy*c       # posicion del sensor en odom
            r = self.cast(wx, wy, yaw + syaw, us_max)        # distancia en su direccion
            vals[name] = r
            rg = Range()
            rg.header.stamp = now; rg.header.frame_id = name
            rg.radiation_type = Range.ULTRASOUND; rg.field_of_view = 0.5
            rg.min_range = 0.02; rg.max_range = us_max; rg.range = float(r)
            self.pub_range[name].publish(rg)
        cen = vals['ultrasound_center']; lef = vals['ultrasound_left']; rig = vals['ultrasound_right']
        d = Distance()
        d.center_distance = cen*100.0; d.left_distance = lef*100.0; d.right_distance = rig*100.0
        d.emergency_stop = (cen*100.0 >= self.get_parameter('emergency_cm').value)  # False = muy cerca
        self.pub_us.publish(d)
        # IR de proximidad como Range (para el collision_monitor): distancia frontal desde base_link, capada corto
        ir_dist = self.cast(x, y, yaw, self.ir_max)
        ir = Range(); ir.header.stamp = now; ir.header.frame_id = 'base_link'
        ir.radiation_type = Range.INFRARED; ir.field_of_view = 0.2
        ir.min_range = 0.02; ir.max_range = self.ir_max; ir.range = float(ir_dist)
        self.pub_ir.publish(ir)
        # --- laser virtual /scan (360) ---
        n = int(self.get_parameter('n_scan').value)
        smax = self.get_parameter('scan_max').value
        ls = LaserScan()
        ls.header.stamp = self.get_clock().now().to_msg()
        ls.header.frame_id = self.get_parameter('scan_frame').value
        ls.angle_min = -math.pi; ls.angle_max = math.pi - (2*math.pi/n)
        ls.angle_increment = 2*math.pi/n
        ls.range_min = 0.02; ls.range_max = smax
        ranges = []
        for i in range(n):
            a = yaw + ls.angle_min + i*ls.angle_increment
            r = self.cast(x, y, a, smax)
            ranges.append(r if r < smax else float('inf'))
        ls.ranges = ranges
        self.pub_scan.publish(ls)

def main():
    rclpy.init(); n = SimSensors()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
