from collections import defaultdict
import ipaddress


class DeviceTrafficStats:

    def __init__(self, lan_network=None, upstream_gateway=None):

        self.lan_network = lan_network
        # The upstream gateway is the internet boundary, not a LAN device, so
        # monitor <-> gateway traffic must count as upload/download, not LOCAL.
        self.upstream_gateway = (
            ipaddress.ip_address(upstream_gateway)
            if upstream_gateway
            else None
        )
        self.stats = defaultdict(
            lambda: {
                "upload": 0,
                "download": 0,
                "total": 0,
                "packets": 0,
            }
        )

    def _is_local(self, ip: str) -> bool:
        """Check if IP is a LAN device (handles /32 suffix).

        The upstream gateway is NOT local: it is the internet boundary.
        """
        if ip is None:
            return False
        clean_ip = ip.split('/')[0]
        try:
            ip_addr = ipaddress.ip_address(clean_ip)
        except ValueError:
            # Fallback for backward compatibility
            return clean_ip.startswith("192.168.137.")

        if self.upstream_gateway is not None and ip_addr == self.upstream_gateway:
            return False

        if self.lan_network is not None:
            try:
                return ip_addr in self.lan_network
            except ValueError:
                return False
        return clean_ip.startswith("192.168.137.")

    def process(self, packet):

        source_ip = packet["source_ip"]
        destination_ip = packet["destination_ip"]

        size = packet["size"]

        source_local = self._is_local(source_ip)
        destination_local = self._is_local(destination_ip)

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
