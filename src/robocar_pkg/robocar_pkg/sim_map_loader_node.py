#!/usr/bin/env python3
# sim_map_loader_node: mete un MAPA REAL guardado (.pgm/.yaml, p.ej. cartografiado y limpiado en el
# editor) en el BANCO de simulacion. Vectoriza el raster a SEGMENTOS (superficies de las paredes) y
# los publica por /sim_map -> el banco lo trata como cualquier mapa dibujado (sim_map_grid rasteriza
# a /map, sim_sensors castea el laser contra ellos, AMCL/Nav2 funcionan igual). Asi se prueban en el
# banco las trayectorias sobre la geometria real (Fase B).
#
#   Publica /sim/maps_list  (String JSON {maps:[nombre]})  cada 3 s
#   Escucha /sim/load_map   (String nombre)  -> vectoriza ~/robocar/maps/<nombre>.pgm -> /sim_map
#   Publica /sim/load_status(String)
import os, glob, json, time, threading
from collections import defaultdict
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from PIL import Image

MAPDIR = os.path.expanduser('~/robocar/maps')


def vectorize(pgm, yaml_path):
    """Raster ocupado -> segmentos de pared (aristas expuestas, fusionadas colineal). Coords mundo."""
    res, ox, oy = 0.05, 0.0, 0.0
    try:
        for line in open(yaml_path):
            s = line.strip()
            if s.startswith('resolution:'):
                res = float(s.split(':', 1)[1])
            elif s.startswith('origin:'):
                v = s.split('[', 1)[1].split(']', 1)[0].split(',')
                ox, oy = float(v[0]), float(v[1])
    except Exception:
        pass
    im = np.array(Image.open(pgm).convert('L'))
    H, W = im.shape
    grid = np.flipud(im < 100)                 # ocupado=oscuro; grid[r,c] r=0 abajo
    segs = []
    for r in range(H):
        for c in range(W):
            if not grid[r, c]:
                continue
            x0 = ox + c * res; y0 = oy + r * res; x1 = x0 + res; y1 = y0 + res
            if c == 0 or not grid[r, c - 1]:     segs.append((x0, y0, x0, y1))
            if c == W - 1 or not grid[r, c + 1]: segs.append((x1, y0, x1, y1))
            if r == 0 or not grid[r - 1, c]:     segs.append((x0, y0, x1, y0))
            if r == H - 1 or not grid[r + 1, c]: segs.append((x0, y1, x1, y1))
    # fusion colineal (horizontales por y, verticales por x)
    out = []
    byy = defaultdict(list)
    for x0, y0, x1, y1 in segs:
        if y0 == y1:
            byy[round(y0, 4)].append((min(x0, x1), max(x0, x1)))
    for y, xs in byy.items():
        xs.sort(); cs = list(xs[0])
        for a, b in xs[1:]:
            if a <= cs[1] + 1e-6:
                cs[1] = max(cs[1], b)
            else:
                out.append([cs[0], y, cs[1], y]); cs = [a, b]
        out.append([cs[0], y, cs[1], y])
    byx = defaultdict(list)
    for x0, y0, x1, y1 in segs:
        if x0 == x1:
            byx[round(x0, 4)].append((min(y0, y1), max(y0, y1)))
    for x, ys in byx.items():
        ys.sort(); cs = list(ys[0])
        for a, b in ys[1:]:
            if a <= cs[1] + 1e-6:
                cs[1] = max(cs[1], b)
            else:
                out.append([x, cs[0], x, cs[1]]); cs = [a, b]
        out.append([x, cs[0], x, cs[1]])
    return out


class SimMapLoader(Node):
    def __init__(self):
        super().__init__('sim_map_loader')
        self.list_pub = self.create_publisher(String, '/sim/maps_list', 10)
        self.map_pub = self.create_publisher(String, '/sim_map', 10)
        self.obs_pub = self.create_publisher(String, '/sim_obstacles', 10)
        self.st_pub = self.create_publisher(String, '/sim/load_status', 10)
        self.create_subscription(String, '/sim/load_map', self._on_load, 10)
        self._busy = False
        self.create_timer(3.0, self._publish_list)
        self.get_logger().info('sim_map_loader listo')
        self._publish_list()

    def st(self, m):
        self.get_logger().info('sim_load: ' + m)
        self.st_pub.publish(String(data=m))

    def _publish_list(self):
        maps = sorted(os.path.basename(m)[:-4] for m in glob.glob(os.path.join(MAPDIR, '*.pgm')))
        self.list_pub.publish(String(data=json.dumps({'maps': maps})))

    def _on_load(self, msg):
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=lambda: self._do_load(msg.data.strip()), daemon=True).start()

    def _do_load(self, name):
        try:
            pgm = os.path.join(MAPDIR, name + '.pgm')
            if not os.path.exists(pgm):
                self.st('ERROR: no existe ' + name + '.pgm'); return
            self.st('vectorizando ' + name + '...')
            segs = vectorize(pgm, os.path.join(MAPDIR, name + '.yaml'))
            self.obs_pub.publish(String(data=json.dumps({'segments': []})))
            self.map_pub.publish(String(data=json.dumps({'segments': segs})))
            self.st('mapa real "%s" cargado en el banco (%d segmentos)' % (name, len(segs)))
        except Exception as e:
            self.st('ERROR cargar: ' + str(e)[:70])
        finally:
            self._busy = False


def main():
    rclpy.init()
    n = SimMapLoader()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
