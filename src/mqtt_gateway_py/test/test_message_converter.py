
"""Unit tests for MQTT message conversion."""

from datetime import datetime, timedelta, timezone
import json

from geometry_msgs.msg import Twist
from mqtt_gateway_py.message_converter import (
    decode_velocity_command,
    encode_safe_velocity_command,
)
import pytest


def make_payload(offset_seconds=0, **changes):
    """Create a valid MQTT command with optional changes."""
    timestamp = (
        datetime.now(timezone.utc)
        + timedelta(seconds=offset_seconds)
    ).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    data = {
        'schema_version': '1.0',
        'command_id': 'test-command-001',
        'timestamp': timestamp,
        'linear_x': 0.8,
        'angular_z': 0.3,
    }
    data.update(changes)
    return json.dumps(data).encode('utf-8')


def test_valid_command():
    """Accept a valid MQTT velocity command."""
    msg, command_id = decode_velocity_command(make_payload())

    assert command_id == 'test-command-001'
    assert msg.linear.x == pytest.approx(0.8)
    assert msg.angular.z == pytest.approx(0.3)


def test_stale_command():
    """Reject commands older than the permitted age."""
    with pytest.raises(ValueError, match='Stale MQTT command'):
        decode_velocity_command(make_payload(offset_seconds=-10))


def test_future_command():
    """Reject commands too far in the future."""
    with pytest.raises(ValueError, match='too far in the future'):
        decode_velocity_command(make_payload(offset_seconds=10))


def test_invalid_json():
    """Reject malformed JSON."""
    with pytest.raises(ValueError, match='Invalid MQTT JSON'):
        decode_velocity_command(b'{"schema_version":')


def test_boolean_velocity():
    """Reject boolean values in velocity fields."""
    with pytest.raises(ValueError, match='Invalid numeric field'):
        decode_velocity_command(make_payload(linear_x=True))


def test_non_finite_velocity():
    """Reject non-finite velocity values."""
    with pytest.raises(ValueError, match='Non-finite value'):
        decode_velocity_command(make_payload(linear_x=float('nan')))


def test_encode_safe_velocity():
    """Encode a ROS2 velocity command as MQTT JSON."""
    msg = Twist()
    msg.linear.x = 1.0
    msg.angular.z = 0.5

    data = json.loads(encode_safe_velocity_command(msg))

    assert data['schema_version'] == '1.0'
    assert data['event_type'] == 'safe_velocity_command'
    assert data['linear_x'] == pytest.approx(1.0)
    assert data['angular_z'] == pytest.approx(0.5)
    assert data['timestamp'].endswith('Z')
