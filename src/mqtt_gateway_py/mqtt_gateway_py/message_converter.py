"""Convert MQTT JSON and ROS2 velocity commands."""

from datetime import datetime, timezone
import json
import math

from geometry_msgs.msg import Twist


MAX_COMMAND_AGE_SECONDS = 2.0
MAX_FUTURE_SKEW_SECONDS = 1.0


def decode_velocity_command(payload):
    """Validate an MQTT command and return its Twist and command ID."""
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

    if (
        not isinstance(timestamp, str)
        or not timestamp.endswith('Z')
        or 'T' not in timestamp
    ):
        raise ValueError(
            'Timestamp must be a UTC ISO8601 string ending in Z'
        )

    try:
        command_time = datetime.fromisoformat(
            timestamp.replace('Z', '+00:00')
        )
    except ValueError as exc:
        raise ValueError('Invalid timestamp format') from exc

    if (
        command_time.tzinfo is None
        or command_time.utcoffset().total_seconds() != 0
    ):
        raise ValueError('Timestamp must use UTC')

    now = datetime.now(timezone.utc)
    age_seconds = (now - command_time).total_seconds()

    if age_seconds > MAX_COMMAND_AGE_SECONDS:
        raise ValueError('Stale MQTT command')

    if age_seconds < -MAX_FUTURE_SKEW_SECONDS:
        raise ValueError('MQTT timestamp is too far in the future')

    values = {}

    for field in ('linear_x', 'angular_z'):
        value = data.get(field)

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
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

    return msg, command_id


def encode_safe_velocity_command(msg):
    """Convert a ROS2 safe velocity command to MQTT JSON."""
    linear_x = float(msg.linear.x)
    angular_z = float(msg.angular.z)

    if not math.isfinite(linear_x) or not math.isfinite(angular_z):
        raise ValueError('Non-finite ROS2 velocity command')

    timestamp = datetime.now(timezone.utc).isoformat(
        timespec='milliseconds'
    ).replace('+00:00', 'Z')

    data = {
        'schema_version': '1.0',
        'event_type': 'safe_velocity_command',
        'timestamp': timestamp,
        'linear_x': linear_x,
        'angular_z': angular_z
    }

    return json.dumps(
        data,
        separators=(',', ':'),
        allow_nan=False
    )
