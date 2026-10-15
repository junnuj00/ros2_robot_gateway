"""MQTT client for the ROS2 robot gateway."""

from queue import Empty, Full, Queue
import time

import paho.mqtt.client as mqtt


class MqttCommandClient:
    """Manage MQTT command reception separately from ROS2."""

    def __init__(
        self,
        host='127.0.0.1',
        port=1883,
        topic='robot/commands/velocity'
    ):
        self.host = host
        self.port = port
        self.topic = topic

        # 수신 메시지 보관용 큐
        self.message_queue = Queue(maxsize=100)

        # paho-mqtt 1.6.1 API
        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # 연결이 끊어졌을 때 재시도 간격
        self.client.reconnect_delay_set(
            min_delay=1,
            max_delay=10
        )

    def on_connect(self, client, userdata, flags, rc):
        """Subscribe to commands after MQTT connection."""
        if rc == 0:
            result, _ = client.subscribe(
                self.topic,
                qos=1
            )

            if result == mqtt.MQTT_ERR_SUCCESS:
                print(f'MQTT subscribed: {self.topic}')
            else:
                print(f'MQTT subscribe failed: {result}')
        else:
            print(f'MQTT connection failed: {rc}')

    def on_message(self, client, userdata, message):
        """Store received messages without blocking."""
        try:
            self.message_queue.put_nowait(message.payload)
        except Full:
            print('MQTT message queue full. Message dropped.')

    def get_message(self):
        """Return the next received message if available."""
        try:
            return self.message_queue.get_nowait()
        except Empty:
            return None

    def start(self):
        """Connect and start the MQTT network loop."""
        self.client.connect(
            self.host,
            self.port,
            keepalive=60
        )
        self.client.loop_start()

    def stop(self):
        """Disconnect and stop the MQTT network loop."""
        self.client.disconnect()
        self.client.loop_stop()


def main():
    """Run a standalone MQTT reception test."""
    mqtt_client = MqttCommandClient()

    try:
        mqtt_client.start()
        print('MQTT client started. Press Ctrl+C to stop.')

        while True:
            payload = mqtt_client.get_message()

            if payload is not None:
                try:
                    print(
                        'Received JSON:',
                        payload.decode('utf-8')
                    )
                except UnicodeDecodeError:
                    print('Invalid UTF-8 MQTT message.')

            time.sleep(0.1)

    except KeyboardInterrupt:
        print('\nStopping MQTT client.')

    finally:
        mqtt_client.stop()


if __name__ == '__main__':
    main()
