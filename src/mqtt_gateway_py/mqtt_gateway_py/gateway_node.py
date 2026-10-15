"""ROS2 gateway for MQTT velocity commands."""

from collections import OrderedDict
import time

from geometry_msgs.msg import Twist
from mqtt_gateway_py.message_converter import (
    decode_velocity_command,
    encode_safe_velocity_command,
)
from mqtt_gateway_py.mqtt_client import MqttCommandClient
import rclpy
from rclpy.node import Node


DUPLICATE_CACHE_SECONDS = 10.0
MAX_RECENT_COMMAND_IDS = 1000


class MqttGatewayNode(Node):
    """Connect MQTT commands and ROS2 velocity topics."""

    def __init__(self):
        super().__init__('mqtt_gateway_node')

        # Recent command IDs for duplicate detection
        self.recent_command_ids = OrderedDict()

        # ROS2 Publisher
        self.command_publisher = self.create_publisher(
            Twist,
            '/robot/cmd_vel',
            10
        )

        # ROS2 Subscriber
        self.safe_command_subscriber = self.create_subscription(
            Twist,
            '/robot/safe_cmd_vel',
            self.handle_safe_command,
            10
        )

        # MQTT Client
        self.mqtt_client = MqttCommandClient()

        # MQTT message queue processing
        self.mqtt_timer = self.create_timer(
            0.1,
            self.process_mqtt_messages
        )

        # Demo mode
        self.declare_parameter('demo_mode', False)

        if self.get_parameter('demo_mode').value:
            self.demo_timer = self.create_timer(
                2.0,
                self.send_demo_command
            )

        self.mqtt_client.start()
        self.get_logger().info('Python MQTT Gateway started.')

    def is_duplicate_command(self, command_id):
        """Check and remember recently accepted command IDs."""
        now = time.monotonic()

        # Remove expired command IDs
        while self.recent_command_ids:
            oldest_id, seen_at = next(
                iter(self.recent_command_ids.items())
            )

            if now - seen_at <= DUPLICATE_CACHE_SECONDS:
                break

            self.recent_command_ids.popitem(last=False)

        if command_id in self.recent_command_ids:
            return True

        # Remember the accepted command
        self.recent_command_ids[command_id] = now

        # Keep memory usage bounded
        if len(self.recent_command_ids) > MAX_RECENT_COMMAND_IDS:
            self.recent_command_ids.popitem(last=False)

        return False

    def process_mqtt_messages(self):
        """Validate MQTT messages and publish ROS2 commands."""
        for _ in range(10):
            payload = self.mqtt_client.get_message()

            if payload is None:
                break

            try:
                msg, command_id = decode_velocity_command(payload)
            except ValueError as exc:
                self.get_logger().warning(
                    f'Rejected MQTT command: {exc}'
                )
                continue

            if self.is_duplicate_command(command_id):
                self.get_logger().warning(
                    'Rejected duplicate MQTT command'
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
        """Forward validated ROS2 commands to MQTT."""
        self.get_logger().info(
            f'Received safe command: '
            f'linear={msg.linear.x:.2f}, '
            f'angular={msg.angular.z:.2f}'
        )

        try:
            payload = encode_safe_velocity_command(msg)
        except ValueError as exc:
            self.get_logger().warning(
                f'Rejected ROS2 event: {exc}'
            )
            return

        if not self.mqtt_client.publish_event(payload):
            self.get_logger().warning(
                'MQTT event could not be queued.'
            )
            return

        self.get_logger().info(
            f'ROS2 -> MQTT event queued: '
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
