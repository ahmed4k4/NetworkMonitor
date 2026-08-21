from datetime import datetime

from .arp import scan_network
from .hostname import resolve_hostname


class DeviceScanner:

    def __init__(self, network, interface):
        self.network = network
        self.interface = interface

    def scan(self):

        raw_devices = scan_network(
            self.network,
            self.interface,
        )

        devices = []

        for item in raw_devices:

            ip = item["ip"]
            mac = item["mac"]

            hostname = resolve_hostname(ip)

            devices.append(
                {
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "last_seen": datetime.now(),
                }
            )

        return devices