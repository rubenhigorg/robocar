#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# particle_relay: AMCL publica /particle_cloud con QoS BEST_EFFORT, que rosbridge (RELIABLE)
# NO recibe -> la web no veria la nube. Este relay la reescucha (best-effort) y la republica
# como /particle_cloud_viz con QoS RELIABLE (compatible con rosbridge), decimada para aliviar.
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav2_msgs.msg import ParticleCloud


class ParticleRelay(Node):
    def __init__(self):
        super().__init__('particle_relay')
        be = QoSProfile(depth=1)
        be.reliability = ReliabilityPolicy.BEST_EFFORT
        be.durability = DurabilityPolicy.VOLATILE
        self.pub = self.create_publisher(ParticleCloud, '/particle_cloud_viz', 10)   # RELIABLE por defecto
        self.create_subscription(ParticleCloud, '/particle_cloud', self.cb, be)
        self.get_logger().info('particle_relay listo (/particle_cloud BE -> /particle_cloud_viz RELIABLE)')

    def cb(self, m):
        m.particles = m.particles[::6]   # decimar (~3000 -> ~500) para la web/rosbridge
        self.pub.publish(m)


def main():
    rclpy.init(); n = ParticleRelay()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
