from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


class MqttGatewayNode(Node):

    def __init__(self):
        super().__init__('mqtt_gateway_node')

        # C++ 제어 노드로 이동 명령 전송
        self.command_publisher = self.create_publisher(
            Twist,
            '/robot/cmd_vel',
            10
        )

        # C++ 제어 노드에서 검증한 명령 수신
        self.safe_command_subscriber = self.create_subscription(
            Twist,
            '/robot/safe_cmd_vel',
            self.handle_safe_command,
            10
        )

        # 테스트 모드는 기본적으로 비활성화
        self.declare_parameter('demo_mode', False)

        if self.get_parameter('demo_mode').value:
            self.demo_timer = self.create_timer(
                2.0,
                self.send_demo_command
            )

        self.get_logger().info('Python Gateway Node started.')

    def publish_velocity(self, linear_x, angular_z):
        """ROS2 이동 명령 발행."""
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)

        self.command_publisher.publish(msg)

        self.get_logger().info(
            f'Published command: '
            f'linear={linear_x:.2f}, angular={angular_z:.2f}'
        )

    def handle_safe_command(self, msg):
        """C++에서 검증한 이동 명령 수신."""
        self.get_logger().info(
            f'Received safe command: '
            f'linear={msg.linear.x:.2f}, '
            f'angular={msg.angular.z:.2f}'
        )

    def send_demo_command(self):
        """테스트용 이동 명령을 한 번만 발행."""
        self.demo_timer.cancel()
        self.publish_velocity(2.0, 0.5)


def main(args=None):
    rclpy.init(args=args)

    node = MqttGatewayNode()

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
