#!/usr/bin/env python3
# slam_checkpoint_node: guarda "checkpoints" del estado de Cartographer (.pbstream) para SOBREVIVIR
# A DERRAPES. En cuanto una rueda patina, la odometria miente y el mapa deja de ser valido; con
# checkpoints frecuentes un derrape solo cuesta lo mapeado desde el ultimo guardado.
#
#   /slam/checkpoint       (std_msgs/Empty)  -> guarda AHORA
#   /slam/checkpoint_auto  (std_msgs/Bool)   -> activa/desactiva el guardado automatico (cada 30 s)
#   /slam/checkpoint_status(std_msgs/String) -> estado legible para la web
#
# Los .pbstream se guardan en ~/robocar/maps/checkpoints/ y se rotan (se conservan los ultimos N).
# Reanudar:  bash ~/robocar/scripts/bringupSLAM.sh --resume-latest   (o --resume <fichero.pbstream>)
import os, glob, time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty, Bool, String
from cartographer_ros_msgs.srv import WriteState


class Ckpt(Node):
    def __init__(self):
        super().__init__('slam_checkpoint')
        self.declare_parameter('dir', os.path.expanduser('~/robocar/maps/checkpoints'))
        self.declare_parameter('keep', 8)
        self.declare_parameter('auto_interval', 30.0)   # s entre checkpoints automaticos
        self.dir = self.get_parameter('dir').value
        os.makedirs(self.dir, exist_ok=True)
        self.keep = int(self.get_parameter('keep').value)
        self.interval = float(self.get_parameter('auto_interval').value)
        self.cli = self.create_client(WriteState, '/write_state')
        self.pub = self.create_publisher(String, '/slam/checkpoint_status', 10)
        self.create_subscription(Empty, '/slam/checkpoint', lambda m: self.save('manual'), 10)
        self.create_subscription(Bool, '/slam/checkpoint_auto', self._toggle, 10)
        self._busy = False
        self._timer = None
        self.get_logger().info('slam_checkpoint listo (dir=%s, keep=%d)' % (self.dir, self.keep))
        self.status('listo')

    def status(self, msg):
        self.get_logger().info('checkpoint: ' + msg)
        self.pub.publish(String(data=msg))

    def _toggle(self, m):
        if m.data and self._timer is None:
            self._timer = self.create_timer(self.interval, lambda: self.save('auto'))
            self.status('auto ON (cada %ds)' % int(self.interval))
        elif not m.data and self._timer is not None:
            self._timer.cancel(); self._timer = None
            self.status('auto OFF')

    def save(self, tag):
        if self._busy:
            return
        if not (self.cli.service_is_ready() or self.cli.wait_for_service(timeout_sec=2.0)):
            self.status('ERROR: /write_state no disponible (arranco cartographer?)'); return
        self._busy = True
        fn = os.path.join(self.dir, 'ckpt_%s.pbstream' % time.strftime('%Y%m%d_%H%M%S'))
        req = WriteState.Request()
        req.filename = fn
        req.include_unfinished_submaps = True
        fut = self.cli.call_async(req)

        def done(f):
            self._busy = False
            try:
                f.result()
                ok = os.path.exists(fn) and os.path.getsize(fn) > 0
                self.rotate()
                self.status('%s guardado (%s)' % (os.path.basename(fn), tag) if ok
                            else 'aviso: %s no aparecio' % os.path.basename(fn))
            except Exception as e:
                self.status('ERROR al guardar: %s' % str(e)[:60])
        fut.add_done_callback(done)

    def rotate(self):
        files = sorted(glob.glob(os.path.join(self.dir, 'ckpt_*.pbstream')))
        for old in files[:-self.keep] if self.keep > 0 else []:
            try:
                os.remove(old)
            except Exception:
                pass


def main():
    rclpy.init()
    n = Ckpt()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
