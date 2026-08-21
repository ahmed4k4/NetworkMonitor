from collections import defaultdict


class DeviceTrafficStats:

    def __init__(self):

        self.stats = defaultdict(
            lambda: {
                "upload": 0,
                "download": 0,
                "total": 0,
                "packets": 0,
            }
        )

    def process(self, packet):

        source_ip = packet["source_ip"]
        destination_ip = packet["destination_ip"]

        size = packet["size"]

        source_local = source_ip.startswith(
            "192.168.137."
        )

        destination_local = destination_ip.startswith(
            "192.168.137."
        )

        if source_local and not destination_local:

            self.stats[source_ip]["upload"] += size

            self.stats[source_ip]["total"] += size

            self.stats[source_ip]["packets"] += 1

        elif not source_local and destination_local:

            self.stats[destination_ip]["download"] += size

            self.stats[destination_ip]["total"] += size

            self.stats[destination_ip]["packets"] += 1

    def get(self, ip):

        return self.stats[ip]

    def all(self):

        return dict(self.stats)