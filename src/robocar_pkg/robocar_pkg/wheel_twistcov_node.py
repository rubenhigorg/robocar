import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped, TwistWithCovarianceStamped


class WheelTwistCov(Node):
    """Adapta /wheel_speed (TwistStamped del encoder) a TwistWithCovarianceStamped
    para que robot_localization (EKF) pueda consumir la velocidad de la rueda.

    El EKF no acepta TwistStamped (sin covarianza). Se republica la vx del
    encoder con una varianza configurable; el resto de componentes llevan
    varianza grande (ademas el twist_config del EKF solo selecciona vx).

    El encoder es de un solo canal (sin signo): la velocidad es siempre >= 0.
    """

    BIG = 1e6

    def __init__(self):
        super().__init__('wheel_twistcov_node')
        self.declare_parameter('input_topic', 'wheel_speed')
        self.declare_parameter('output_topic', 'wheel_speed_cov')
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('vx_variance', 0.02)     # (m/s)^2

        inp = self.get_parameter('input_topic').value
        out = self.get_parameter('output_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.vx_var = float(self.get_parameter('vx_variance').value)

        self.pub = self.create_publisher(TwistWithCovarianceStamped, out, 10)
        self.sub = self.create_subscription(TwistStamped, inp, self.callback, 10)
        self.get_logger().info(
            'wheel_twistcov_node: %s (TwistStamped) -> %s (TwistWithCovarianceStamped), frame=%s'
            % (inp, out, self.frame_id))

    def callback(self, msg):
        out = TwistWithCovarianceStamped()
        out.header.stamp = msg.header.stamp
        out.header.frame_id = self.frame_id
        out.twist.twist = msg.twist

        cov = [0.0] * 36
        cov[0] = self.vx_var     # vx
        cov[7] = self.BIG        # vy
        cov[14] = self.BIG       # vz
        cov[21] = self.BIG       # vroll
        cov[28] = self.BIG       # vpitch
        cov[35] = self.BIG       # vyaw
        out.twist.covariance = cov
        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = WheelTwistCov()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
