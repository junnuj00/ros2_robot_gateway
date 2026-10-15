"""Validate MQTT commands and convert them to ROS2 messages."""

from datetime import datetime
import json
import math

from geometry_msgs.msg import Twist


def decode_velocity_command(payload):
    """Convert a validated MQTT JSON command to ROS2 Twist."""
    try:
        data = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid MQTT JSON payload') from exc

    if not isinstance(data, dict):
        raise ValueError('Command must be a JSON object')

    if data.get('schema_version') != '1.0':
        raise ValueError('Unsupported schema version')

    command_id = data.get('command_id')

    if not isinstance(command_id, str) or not command_id.strip():
        raise ValueError('Invalid command_id')

    timestamp = data.get('timestamp')

    if not isinstance(timestamp, str) or not timestamp.endswith('Z'):
        raise ValueError('Timestamp must be a UTC string ending in Z')

    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid timestamp format') from exc

    values = {}

    for field in ('linear_x', 'angular_z'):
        value = data.get(field)

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'Invalid numeric field: {field}')

        try:
            number = float(value)
        except OverflowError as exc:
            raise ValueError(f'Numeric overflow: {field}') from exc

        if not math.isfinite(number):
            raise ValueError(f'Non-finite value: {field}')

        values[field] = number

    msg = Twist()
    msg.linear.x = values['linear_x']
    msg.angular.z = values['angular_z']

    return msg
