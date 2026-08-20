#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# map_areas: CONTRATO de ZONAS del mapa (cocina, bano, salon...), consumible por la WEB hoy
# y por el LLM manana (Capa 3). Es la pieza de RESOLUCION SEMANTICA de la Capa 2: nombre->pose.
#
#   /map_areas      (String JSON, latched) -> lista de zonas: [{name, rect:[x0,y0,x1,y1], goal:[cx,cy]}]
#   /map_areas/set  (String JSON)          -> operaciones:
#         {"op":"add","name":"cocina","rect":[x0,y0,x1,y1]}   (anade/reemplaza por nombre)
#         {"op":"del","name":"cocina"}                        (borra una)
#         {"op":"clear"}                                      (borra todas)
#         {"areas":[...]}                                     (reemplaza toda la lista)
#   Coordenadas en frame 'map' (mismas que /goal_pose). Persiste en ~/.robocar_map_areas.json.
#
# Uso por el LLM (futuro): navigate_to("cocina") -> busca la zona -> su goal -> /goal_pose;
#   where_am_i(pose) -> test punto-en-rect -> "estas en el salon".
import json, os, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

STORE = os.path.expanduser('~/.robocar_map_areas.json')


def norm_rect(r):
    x0, y0, x1, y1 = float(r[0]), float(r[1]), float(r[2]), float(r[3])
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def with_goal(a):
    r = norm_rect(a['rect'])
    return {'name': str(a['name']).strip().lower(),
            'rect': r,
            'goal': [round((r[0] + r[2]) / 2.0, 3), round((r[1] + r[3]) / 2.0, 3)]}


class MapAreas(Node):
    def __init__(self):
        super().__init__('map_areas')
        self.areas = self._load()
        qos = QoSProfile(depth=1); qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.pub = self.create_publisher(String, '/map_areas', qos)
        self.create_subscription(String, '/map_areas/set', self.on_set, 10)
        self.publish_areas()
        self.get_logger().info('map_areas listo (%d zonas). GET /map_areas, SET /map_areas/set' % len(self.areas))

    def _load(self):
        try:
            return [with_goal(a) for a in json.load(open(STORE)).get('areas', [])]
        except Exception:
            return []

    def _save(self):
        try:
            json.dump({'areas': self.areas}, open(STORE, 'w'))
        except Exception as e:
            self.get_logger().warn('no puedo guardar zonas: %s' % e)

    def publish_areas(self):
        m = String(); m.data = json.dumps({'areas': self.areas}); self.pub.publish(m)

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
