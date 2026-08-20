#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# map_areas: guardian del BUNDLE "mapa + zonas". Persiste JUNTOS el mapa dibujado y sus zonas
# (cocina, bano, salon...) para que se recuperen a la vez. Contrato (como /nav_config) para la
# WEB hoy y el LLM manana (Capa 3): resolucion semantica nombre->pose.
#
#   /map_areas      (String JSON, latched) -> zonas: [{name, rect:[x0,y0,x1,y1], goal:[cx,cy]}]
#   /map_areas/set  (String JSON)          -> add / del / clear / reemplazo de zonas
#   /sim_map        (String JSON)          -> lo ESCUCHA (para guardar el mapa) y lo REEMITE al
#                                             arrancar (para recuperar el mapa persistido).
#   Persistencia en ~/.robocar_map_bundle.json = {"map": {...}, "areas": [...]}.
#
# Coordenadas en frame 'map' (mismas que /goal_pose). Uso por el LLM (futuro):
#   navigate_to("cocina") -> centroide -> /goal_pose;  where_am_i(pose) -> punto-en-rect.
import json, os, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

STORE = os.path.expanduser('~/.robocar_map_bundle.json')


def norm_rect(r):
    x0, y0, x1, y1 = float(r[0]), float(r[1]), float(r[2]), float(r[3])
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def with_goal(a):
    r = norm_rect(a['rect'])
    return {'name': str(a['name']).strip().lower(), 'rect': r,
            'goal': [round((r[0] + r[2]) / 2.0, 3), round((r[1] + r[3]) / 2.0, 3)]}


class MapAreas(Node):
    def __init__(self):
        super().__init__('map_areas')
        self.areas, self.map_json = self._load()
        qos = QoSProfile(depth=1); qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.pub = self.create_publisher(String, '/map_areas', qos)
        self.pub_map = self.create_publisher(String, '/sim_map', 10)
        self.create_subscription(String, '/map_areas/set', self.on_set, 10)
        self.create_subscription(String, '/sim_map', self.on_map, 10)
        self.publish_areas()
        # reemitir el mapa guardado una vez, cuando sim_map_grid/sim_sensors y la odometria esten listos
        self._replay_timer = self.create_timer(4.0, self._replay)
        self.get_logger().info('map_areas listo (%d zonas, mapa %s). GET /map_areas, SET /map_areas/set'
                               % (len(self.areas), 'guardado' if self.map_json else 'vacio'))

    def _load(self):
        try:
            d = json.load(open(STORE))
            return [with_goal(a) for a in d.get('areas', [])], d.get('map')
        except Exception:
            return [], None

    def _save(self):
        try:
            json.dump({'map': self.map_json, 'areas': self.areas}, open(STORE, 'w'))
        except Exception as e:
            self.get_logger().warn('no puedo guardar bundle: %s' % e)

    def publish_areas(self):
        m = String(); m.data = json.dumps({'areas': self.areas}); self.pub.publish(m)

    def _replay(self):
        self._replay_timer.cancel()
        if self.map_json:
            m = String(); m.data = json.dumps(self.map_json); self.pub_map.publish(m)
            self.get_logger().info('mapa persistido reemitido (%d segmentos)' % len(self.map_json.get('segments', [])))

    def on_map(self, msg):
        try:
            d = json.loads(msg.data); segs = d.get('segments', [])
        except Exception:
            return
        newmap = {'segments': segs} if segs else None
        if newmap != self.map_json:
            self.map_json = newmap; self._save()

    def on_set(self, msg):
        try:
            d = json.loads(msg.data)
        except Exception:
            return
        try:
            if 'areas' in d:
                self.areas = [with_goal(a) for a in d['areas']]
            else:
                op = d.get('op')
                if op == 'clear':
                    self.areas = []
                elif op == 'del':
                    nm = str(d.get('name', '')).strip().lower()
                    self.areas = [a for a in self.areas if a['name'] != nm]
                elif op == 'add':
                    a = with_goal(d)
                    self.areas = [x for x in self.areas if x['name'] != a['name']] + [a]
        except Exception as e:
            self.get_logger().warn('set invalido: %s' % e); return
        self._save(); self.publish_areas()
        self.get_logger().info('zonas: %s' % ', '.join(a['name'] for a in self.areas))


def main():
    rclpy.init(); n = MapAreas()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
