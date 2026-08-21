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
import numpy as np
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import String
from messages_pkg.msg import Distance

def cast_rays(px, py, dirs, segs):
    """Ray-casting VECTORIZADO: para R rayos (mismo origen px,py, direcciones unitarias
    dirs (R,2)) contra S segmentos (S,4)=[ax,ay,bx,by], devuelve la distancia al mas cercano
    de cada rayo (R,), inf si no corta ninguno. Todo en numpy (una pasada en C)."""
    R = dirs.shape[0]
    if segs.shape[0] == 0:
        return np.full(R, np.inf)
    ax, ay, bx, by = segs[:, 0], segs[:, 1], segs[:, 2], segs[:, 3]   # (S,)
    ex, ey = bx - ax, by - ay
    apx, apy = ax - px, ay - py
    Dx = dirs[:, 0:1]; Dy = dirs[:, 1:2]                # (R,1)
    den = Dx * ey[None, :] - Dy * ex[None, :]           # (R,S)
    safe = np.abs(den) > 1e-9
    den_s = np.where(safe, den, 1.0)
    t = (apx * ey - apy * ex)[None, :] / den_s          # (R,S)
    u = (apx[None, :] * Dy - apy[None, :] * Dx) / den_s # (R,S)
    valid = safe & (t >= 0.0) & (u >= 0.0) & (u <= 1.0)
    return np.where(valid, t, np.inf).min(axis=1)       # (R,)

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
        self._segarr = np.zeros((0, 4))   # cache numpy de (segs+obs) para el ray-cast vectorizado
        self.pose = None   # pose REAL del robot (de /truth_pose, la publica sim_motion)
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
        self.create_subscription(PoseStamped, '/truth_pose', self.tpcb, 20)   # pose REAL (sim_motion)
        self.create_subscription(String, '/sim_map', self.mcb, 10)
        self.create_subscription(String, '/sim_obstacles', self.obcb, 10)
        rate = self.get_parameter('rate_hz').value
        self.create_timer(1.0/rate, self.tick)
        self.get_logger().info('sim_sensors listo (mapa por /sim_map, publica /ultrasound_data + /scan)')

    def tpcb(self, m):
        # pose REAL del robot (la publica sim_motion en /truth_pose). Los sensores se lanzan de aqui,
        # NO de la odometria (que puede derivar). Asi AMCL tiene deriva real que corregir.
        p = m.pose; q = p.orientation
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
        self._rebuild_arr()
        self.get_logger().info('MAPA recibido: %d paredes.' % len(self.segs))

    def obcb(self, msg):
        # obstaculos dinamicos: mismo formato/transform que el mapa, pero solo afectan al /scan
        if self.pose is None:
            return
        try:
            rel = json.loads(msg.data).get('segments', [])
        except Exception:
            return
        # el web envia coords ABSOLUTAS (frame odom0/map, igual que /truth_pose): NO re-transformar
        # por la pose actual. Si no, un obstaculo pintado a media navegacion queda desplazado lo que el
        # robot lleva avanzado y el robot pasa por encima. (El mapa se libra porque se envia con el robot
        # en el origen -> transform identidad.)
        self.obs = [(q[0], q[1], q[2], q[3]) for q in rel]
        self._rebuild_arr()
        self.get_logger().info('OBSTACULOS: %d' % len(self.obs))

    def _rebuild_arr(self):
        allsegs = self.segs + self.obs
        self._segarr = np.array(allsegs, dtype=float) if allsegs else np.zeros((0, 4))

    def cast(self, px, py, ang, maxd):
        """Un solo rayo (para ultrasonidos/IR): usa el mismo ray-cast vectorizado y capa a maxd.
        Devuelve float NATIVO (no np.float64) para no romper los campos tipados del mensaje."""
        d = np.array([[math.cos(ang), math.sin(ang)]])
        r = cast_rays(px, py, d, self._segarr)[0]
        return float(maxd if r > maxd else r)

    def tick(self):
        if self.pose is None:
            return
        x, y, yaw = self.pose   # pose REAL (de sim_motion): los sensores no conocen la odometria (que deriva)
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
        # 120 rayos de una vez (vectorizado): direcciones absolutas y ray-cast en numpy
        angs = yaw + ls.angle_min + np.arange(n) * ls.angle_increment
        dirs = np.stack([np.cos(angs), np.sin(angs)], axis=1)      # (n,2)
        r = cast_rays(x, y, dirs, self._segarr)                    # (n,) inf donde no corta
        ls.ranges = np.where(r < smax, r, np.inf).tolist()         # fuera de alcance -> inf
        self.pub_scan.publish(ls)

def main():
    rclpy.init(); n = SimSensors()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()
