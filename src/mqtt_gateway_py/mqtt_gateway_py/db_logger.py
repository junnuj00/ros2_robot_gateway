
"""Save MQTT command processing logs to PostgreSQL."""

import logging
from queue import Empty, Full, Queue
from threading import Event, Thread

import psycopg2


INSERT_SQL = """
INSERT INTO command_logs (
    command_id, linear_x, angular_z, status, reason
)
VALUES (%s, %s, %s, %s, %s)
"""


class CommandDbLogger:
    """Write command logs without blocking ROS2 callbacks."""

    def __init__(self, database='robot_gateway_db'):
        self.database = database
        self.queue = Queue(maxsize=100)
        self.stopping = Event()

        self.worker = Thread(
            target=self._run,
            daemon=True
        )
        self.worker.start()

    def log(self, command_id, linear_x, angular_z,
            status, reason=None):
        """Queue a command processing record."""
        record = (
            command_id,
            linear_x,
            angular_z,
            status,
            reason
        )

        try:
            self.queue.put_nowait(record)
            return True
        except Full:
            logging.warning('Database log queue is full')
            return False

    def _run(self):
        """Write queued records using a background thread."""
        connection = None

        while not self.stopping.is_set() or not self.queue.empty():
            try:
                record = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                if connection is None or connection.closed:
                    connection = psycopg2.connect(
                        dbname=self.database,
                        connect_timeout=2
                    )

                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute(INSERT_SQL, record)

            except psycopg2.Error as exc:
                logging.warning(
                    'Database log write failed: %s', exc
                )

                if connection is not None:
                    connection.close()
                connection = None

            finally:
                self.queue.task_done()

        if connection is not None:
            connection.close()

    def close(self):
        """Request worker shutdown."""
        self.stopping.set()
        self.worker.join(timeout=3)

        if self.worker.is_alive():
            logging.warning('Database logger did not finish shutdown')
