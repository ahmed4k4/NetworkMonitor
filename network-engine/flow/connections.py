from datetime import datetime


class ConnectionTracker:

    def __init__(self, timeout=60):

        self.connections = {}
        self.timeout = timeout

    def update(self, flow):

        key = flow.key

        now = datetime.now()

        if key not in self.connections:

            self.connections[key] = {
                "key": key,

                "source_ip": flow.source_ip,
                "destination_ip": flow.destination_ip,

                "source_port": flow.source_port,
                "destination_port": flow.destination_port,

                "protocol": flow.protocol,

                "started_at": flow.started_at,
                "last_seen": now,

                "state": "ACTIVE",
            }

        connection = self.connections[key]

        connection["last_seen"] = now
        connection["state"] = "ACTIVE"

        return connection

    def cleanup(self):

        now = datetime.now()

        for connection in self.connections.values():

            elapsed = (
                now - connection["last_seen"]
            ).total_seconds()

            if elapsed > self.timeout:

                connection["state"] = "CLOSED"

    def active(self):

        return [
            connection
            for connection in self.connections.values()
            if connection["state"] == "ACTIVE"
        ]

    def closed(self):

        return [
            connection
            for connection in self.connections.values()
            if connection["state"] == "CLOSED"
        ]