#!/usr/bin/env python3
# map_edit_node: soporte para el EDITOR DE MAPA de la web (editor.html).
#   Lista checkpoints y mapas guardados, carga uno como rejilla editable, y guarda el mapa
#   retocado a ~/robocar/maps/<nombre>.pgm/.yaml. Asi se limpian los mapas (borrar fugas, cerrar
#   paredes) sin salir a GIMP.
#
#   Publica  /slam/maps_list   (String JSON: {checkpoints:[{name,pose}], maps:[name]})  cada 3 s
#   Escucha  /slam/edit_load   (String "ckpt:<n>" | "map:<n>")  -> publica /edit_map (OccupancyGrid)
#   Escucha  /edited_map        (OccupancyGrid)  -> guarda la ultima recibida
#   Escucha  /slam/edit_save    (String nombre)  -> escribe la editada a maps/<nombre>.pgm/.yaml
#   Publica  /slam/edit_status  (String)  -> estado para la web
import os, glob, json, time, threading, subprocess
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import OccupancyGrid
from PIL import Image

CKDIR = os.path.expanduser('~/robocar/maps/checkpoints')
MAPDIR = os.path.expanduser('~/robocar/maps')


class MapEdit(Node):
    def __init__(self):
        super().__init__('map_edit')
        os.makedirs(MAPDIR, exist_ok=True)
        self.list_pub = self.create_publisher(String, '/slam/maps_list', 10)
        self.map_pub = self.create_publisher(OccupancyGrid, '/edit_map', 1)
        self.st_pub = self.create_publisher(String, '/slam/edit_status', 10)
        self.create_subscription(String, '/slam/edit_load', self._on_load, 10)
        self.create_subscription(OccupancyGrid, '/edited_map', self._on_edited, 1)
        self.create_subscription(String, '/slam/edit_save', self._on_save, 10)
        self.create_subscription(String, '/slam/edit_delete', self._on_delete, 10)
        self._edited = None
        self._busy = False
        self.create_timer(3.0, self._publish_list)
        self.get_logger().info('map_edit listo')
        self._publish_list()

    def st(self, m):
        self.get_logger().info('edit: ' + m)
        self.st_pub.publish(String(data=m))

    # ---------- listado ----------
    def _publish_list(self):
        cks = []
        for pb in sorted(glob.glob(os.path.join(CKDIR, 'ckpt_*.pbstream'))):
            name = os.path.basename(pb)[:-len('.pbstream')]
            pose = None
            jf = pb[:-len('.pbstream')] + '.json'
            if os.path.exists(jf):
                try:
                    pose = json.load(open(jf))
                except Exception:
                    pose = None
            cks.append({'name': name, 'pose': pose})
        maps = sorted(os.path.basename(m)[:-len('.pgm')] for m in glob.glob(os.path.join(MAPDIR, '*.pgm')))
        self.list_pub.publish(String(data=json.dumps({'checkpoints': cks, 'maps': maps})))

    # ---------- cargar para editar ----------
    def _on_load(self, msg):
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=lambda: self._do_load(msg.data.strip()), daemon=True).start()

    def _do_load(self, spec):
        try:
            kind, name = spec.split(':', 1)
            if kind == 'ckpt':
                self.st('convirtiendo checkpoint %s...' % name)
                pb = os.path.join(CKDIR, name + '.pbstream')
                stem = '/tmp/edit_load'
                for f in (stem + '.pgm', stem + '.yaml'):
                    try: os.remove(f)
                    except Exception: pass
                subprocess.run(['ros2', 'run', 'cartographer_ros', 'cartographer_pbstream_to_ros_map',
                                '-pbstream_filename', pb, '-map_filestem', stem, '-resolution', '0.05'],
                               env=os.environ, timeout=40,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                grid = self._pgm_to_grid(stem + '.pgm', stem + '.yaml')
            else:
                base = os.path.join(MAPDIR, name)
                grid = self._pgm_to_grid(base + '.pgm', base + '.yaml')
            if grid is None:
                self.st('ERROR: no pude cargar ' + spec)
            else:
                self.map_pub.publish(grid)
                self.st('cargado %s (%dx%d)' % (spec, grid.info.width, grid.info.height))
        except Exception as e:
            self.st('ERROR cargar: ' + str(e)[:70])
        finally:
            self._busy = False

    def _read_yaml(self, path):
        res, ox, oy, occ, free, neg = 0.05, 0.0, 0.0, 0.65, 0.196, 0
        try:
            for line in open(path):
                s = line.strip()
                if s.startswith('resolution:'):
                    res = float(s.split(':', 1)[1])
                elif s.startswith('origin:'):
                    v = s.split('[', 1)[1].split(']', 1)[0].split(',')
                    ox, oy = float(v[0]), float(v[1])
                elif s.startswith('occupied_thresh:'):
                    occ = float(s.split(':', 1)[1])
                elif s.startswith('free_thresh:'):
                    free = float(s.split(':', 1)[1])
                elif s.startswith('negate:'):
                    neg = int(s.split(':', 1)[1])
        except Exception:
            pass
        return res, ox, oy, occ, free, neg

    def _pgm_to_grid(self, pgm, yaml_path):
        if not os.path.exists(pgm):
            return None
        res, ox, oy, occ_th, free_th, negate = self._read_yaml(yaml_path)
        im = np.array(Image.open(pgm).convert('L'))   # (H, W), fila 0 = arriba
        H, W = im.shape
        p = im.astype(float)
        if negate:
            p = 255.0 - p
        prob = (255.0 - p) / 255.0                     # 0=libre .. 1=ocupado
        data = np.full((H, W), -1, np.int8)
        data[prob > occ_th] = 100
        data[prob < free_th] = 0
        grid_data = np.flipud(data).reshape(-1).astype(np.int8).tolist()   # fila 0 = abajo (origen)
        og = OccupancyGrid()
        og.header.frame_id = 'map'
        og.info.resolution = float(res)
        og.info.width = int(W); og.info.height = int(H)
        og.info.origin.position.x = float(ox); og.info.origin.position.y = float(oy)
        og.info.origin.orientation.w = 1.0
        og.data = grid_data
        return og

    # ---------- borrar ----------
    def _on_delete(self, msg):
        try:
            kind, raw = msg.data.strip().split(':', 1)
            name = ''.join(c for c in raw if c.isalnum() or c in '_-')   # sin rutas
            if not name:
                return
            if kind == 'ckpt':
                paths = [os.path.join(CKDIR, name + '.pbstream'), os.path.join(CKDIR, name + '.json')]
            else:
                paths = [os.path.join(MAPDIR, name + '.pgm'), os.path.join(MAPDIR, name + '.yaml')]
            n = 0
            for p in paths:
                if os.path.exists(p):
                    os.remove(p); n += 1
            self.st('borrado %s (%d ficheros)' % (msg.data.strip(), n))
            self._publish_list()
        except Exception as e:
            self.st('ERROR borrar: ' + str(e)[:60])

    # ---------- guardar el editado ----------
    def _on_edited(self, m):
        self._edited = m

    def _on_save(self, msg):
        name = ''.join(c for c in msg.data.strip() if c.isalnum() or c in '_-') or 'mapa'
        threading.Thread(target=lambda: self._do_save(name), daemon=True).start()

    def _do_save(self, name):
        if self._edited is None:
            self.st('ERROR: no me ha llegado el mapa editado (reintenta)'); return
        try:
            m = self._edited
            W, H = m.info.width, m.info.height
            d = np.array(m.data, dtype=np.int16).reshape(H, W)   # fila 0 = abajo
            img = np.full((H, W), 205, np.uint8)                 # desconocido gris
            img[(d >= 0) & (d < 50)] = 254                       # libre blanco
            img[d >= 50] = 0                                     # ocupado negro
            out = np.flipud(img)                                 # fila 0 imagen = arriba
            base = os.path.join(MAPDIR, name)
            Image.fromarray(out, 'L').save(base + '.pgm')
            with open(base + '.yaml', 'w') as f:
                f.write('image: %s.pgm\nresolution: %.6f\norigin: [%.6f, %.6f, 0.0]\n'
                        'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n'
                        % (name, m.info.resolution, m.info.origin.position.x, m.info.origin.position.y))
            self.st('guardado ~/robocar/maps/%s.pgm (%dx%d)' % (name, W, H))
            self._publish_list()
        except Exception as e:
            self.st('ERROR guardar: ' + str(e)[:70])


def main():
    rclpy.init()
    n = MapEdit()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
