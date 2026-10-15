"""ROS2 gateway for MQTT velocity commands."""

from geometry_msgs.msg import Twist
from mqtt_gateway_py.message_converter import decode_velocity_command
from mqtt_gateway_py.mqtt_client import MqttCommandClient
import rclpy
from rclpy.node import Node


class MqttGatewayNode(Node):
    """Connect MQTT commands to the ROS2 robot controller."""

    def __init__(self):
        super().__init__('mqtt_gateway_node')

        # ROS2 이동 명령 발행
        self.command_publisher = self.create_publisher(
            Twist,
            '/robot/cmd_vel',
            10
        )

        # C++에서 검증한 명령 수신
        self.safe_command_subscriber = self.create_subscription(
            Twist,
            '/robot/safe_cmd_vel',
            self.handle_safe_command,
            10
        )

        # MQTT 통신은 별도 클래스로 관리
        self.mqtt_client = MqttCommandClient()

        # 100ms마다 MQTT 큐 확인
        self.mqtt_timer = self.create_timer(
            0.1,
            self.process_mqtt_messages
        )

        # 기존 테스트 모드 유지
        self.declare_parameter('demo_mode', False)

        if self.get_parameter('demo_mode').value:
            self.demo_timer = self.create_timer(
                2.0,
                self.send_demo_command
            )

        self.mqtt_client.start()
        self.get_logger().info('Python MQTT Gateway started.')

    def process_mqtt_messages(self):
        """Validate queued MQTT messages and publish to ROS2."""
        # 한 번에 최대 10개 처리하여 콜백 독점 방지
        for _ in range(10):
            payload = self.mqtt_client.get_message()

            if payload is None:
                break

            try:
                msg = decode_velocity_command(payload)
            except ValueError as exc:
                self.get_logger().warning(
                    f'Rejected MQTT command: {exc}'
                )
                continue

            self.command_publisher.publish(msg)

            self.get_logger().info(
                f'MQTT -> ROS2: '
                f'linear={msg.linear.x:.2f}, '
                f'angular={msg.angular.z:.2f}'
            )

    def publish_velocity(self, linear_x, angular_z):
        """Publish a ROS2 velocity command."""
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)

        self.command_publisher.publish(msg)

        self.get_logger().info(
            f'Published command: '
            f'linear={msg.linear.x:.2f}, '
            f'angular={msg.angular.z:.2f}'
        )

    def handle_safe_command(self, msg):
        """Receive validated commands from the C++ controller."""
        self.get_logger().info(
            f'Received safe command: '
            f'linear={msg.linear.x:.2f}, '
            f'angular={msg.angular.z:.2f}'
        )

    def send_demo_command(self):
        """Publish one demonstration command."""
        self.demo_timer.cancel()
        self.publish_velocity(2.0, 0.5)


def main(args=None):
    """Start the ROS2 MQTT Gateway."""
    rclpy.init(args=args)
    node = None

    try:
        node = MqttGatewayNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if node is not None:
            node.mqtt_client.stop()
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
