#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Publica /map (nav_msgs/OccupancyGrid) a partir del mapa dibujado por web (/sim_map).
#
# Preparatoria de la Capa 2 (Nav2): el banco debe hablar las MISMAS interfaces que Nav.
# Cartographer (Capa 1) publicara /map como OccupancyGrid; aqui lo generamos rasterizando
# los segmentos-pared que dibuja la web, para poder alimentar la CAPA ESTATICA del costmap
# global de Nav2 con el mismo mapa de banco. Cuando llegue el SLAM real, este nodo se
# retira y Nav2 no cambia (mismo topic, tipo, frame).
#
# Entradas:
#   /sim_map (std_msgs/String, JSON {"segments":[[x1,y1,x2,y2],...]} RELATIVOS a la pose
#            del coche al enviarlo, igual que sim_sensors_node).
#   /odometry/filtered (nav_msgs/Odometry) -> pose actual para anclar el mapa en 'odom'.
# Salidas:
#   /map (nav_msgs/OccupancyGrid, frame 'map', QoS transient_local/latched).
#   TF estatico map->odom (identidad) para que el mapa sea colocable (en real lo da AMCL/SLAM).
import json, math, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
from nav_msgs.msg import Odometry, OccupancyGrid
from std_msgs.msg import String
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


def rasterize(segs, res, margin, wall_cells):
    """Segmentos (en frame mundo) -> (info_origin_x, origin_y, W, H, data[]).
    data: 0=libre, 100=ocupado. wall_cells = radio de engrosado (celdas) de la pared."""
    if not segs:
        return None
    xs = []; ys = []
    for (ax, ay, bx, by) in segs:
        xs += [ax, bx]; ys += [ay, by]
    minx = min(xs) - margin; miny = min(ys) - margin
    maxx = max(xs) + margin; maxy = max(ys) + margin
    W = max(1, int(math.ceil((maxx - minx) / res)))
    H = max(1, int(math.ceil((maxy - miny) / res)))
    data = [0] * (W * H)
    r = int(wall_cells)

    def mark(cx, cy):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x = cx + dx; y = cy + dy
                if 0 <= x < W and 0 <= y < H:
                    data[y * W + x] = 100

    for (ax, ay, bx, by) in segs:
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(math.ceil(L / (res * 0.5))))   # paso <= media celda: sin huecos
        for i in range(n + 1):
            t = i / n
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t
            cx = int((px - minx) / res)
            cy = int((py - miny) / res)
            mark(cx, cy)
    return (minx, miny, W, H, data)


class SimMapGrid(Node):
    def __init__(self):
        super().__init__('sim_map_grid')
        self.declare_parameter('resolution', 0.05)     # m/celda (por defecto Nav2)
        self.declare_parameter('margin', 0.5)          # m de margen libre alrededor
        self.declare_parameter('wall_cells', 1)        # engrosado pared (1 -> ~0.15 m a 0.05)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('publish_map_tf', True) # TF estatico map->odom identidad (banco)
        self.declare_parameter('republish_hz', 1.0)    # re-publica el mapa (robustez ademas de latched)

        self.pose = None
        self.grid = None                               # OccupancyGrid cacheada

        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL   # latched: subs tardios reciben el ultimo
        qos.reliability = QoSReliabilityPolicy.RELIABLE
        qos.history = QoSHistoryPolicy.KEEP_LAST
        self.pub = self.create_publisher(OccupancyGrid, '/map', qos)

        self.create_subscription(Odometry, '/odometry/filtered', self.ocb, 20)
        self.create_subscription(String, '/sim_map', self.mcb, 10)

        if self.get_parameter('publish_map_tf').value:
            self.stf = StaticTransformBroadcaster(self)
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = self.get_parameter('map_frame').value
            t.child_frame_id = self.get_parameter('odom_frame').value
            t.transform.rotation.w = 1.0                # identidad: en banco map == odom
            self.stf.sendTransform(t)

        hz = self.get_parameter('republish_hz').value
        if hz > 0:
            self.create_timer(1.0 / hz, self.republish)
        self.get_logger().info('sim_map_grid listo (dibuja el mapa y "Enviar mapa" -> /map OccupancyGrid)')

    def ocb(self, m):
        p = m.pose.pose; q = p.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose = (p.position.x, p.position.y, yaw)

    def mcb(self, msg):
        if self.pose is None:
            self.get_logger().warn('Sin odometria; ignoro mapa.'); return
        try:
            rel = json.loads(msg.data).get('segments', [])
        except Exception as e:
            self.get_logger().warn('mapa JSON invalido: %s' % e); return
        if not rel:
            # mapa vacio -> LIMPIAR /map (rejilla 1x1 libre): borra la web y el costmap,
            # y deja de republicar el mapa viejo.
            og = OccupancyGrid(); og.header.frame_id = self.get_parameter('map_frame').value
            og.info.resolution = float(self.get_parameter('resolution').value)
            og.info.width = 1; og.info.height = 1; og.info.origin.orientation.w = 1.0
            og.data = [0]
            self.grid = og; self.publish_grid()
            self.get_logger().info('/map limpiado (mapa vacio recibido)'); return
        segs = [(seg[0], seg[1], seg[2], seg[3]) for seg in rel]  # ya en odom (identidad)
        res = self.get_parameter('resolution').value
        margin = self.get_parameter('margin').value
        wc = self.get_parameter('wall_cells').value
        r = rasterize(segs, res, margin, wc)
        if r is None:
            return
        minx, miny, W, H, data = r
        og = OccupancyGrid()
        og.header.frame_id = self.get_parameter('map_frame').value
        og.info.resolution = float(res)
        og.info.width = W; og.info.height = H
        og.info.origin.position.x = float(minx)
        og.info.origin.position.y = float(miny)
        og.info.origin.orientation.w = 1.0
        og.data = data
        self.grid = og
        self.publish_grid()
        self.get_logger().info('/map publicado: %dx%d celdas @ %.2f m (%d paredes)' % (W, H, res, len(segs)))

    def publish_grid(self):
        if self.grid is None:
            return
        self.grid.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.grid)

    def republish(self):
        self.publish_grid()


def main():
    rclpy.init(); n = SimMapGrid()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
