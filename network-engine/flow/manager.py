from datetime import datetime, timezone
import ipaddress

from models.flow import Flow


class FlowManager:

    def __init__(
        self,
        network,
        interface,
        flow_timeout=60,
        upstream_gateway=None,
    ):
        self.network = network
        self.interface = interface
        self.flow_timeout = flow_timeout
        # The upstream router/gateway IP is the boundary to the internet. It is
        # NOT a LAN device, so traffic between the monitor and the gateway must
        # be classified as UPLOAD/DOWNLOAD rather than LOCAL. Without this, every
        # packet seen on the monitor's interface (monitor <-> gateway) is LOCAL
        # and upload/download byte counters stay permanently at 0.
        self.upstream_gateway = (
            ipaddress.ip_address(upstream_gateway)
            if upstream_gateway
            else None
        )
        
        # Parse LAN network from network parameter (e.g., "192.168.137.0/24")
        try:
            self.lan_network = ipaddress.ip_network(network, strict=False)
        except ValueError:
            # Fallback to default
            self.lan_network = ipaddress.ip_network("192.168.137.0/24", strict=False)

        self.flows = {}

    def _is_local(self, ip: str) -> bool:
        """Check if IP is a LAN device (handles /32 suffix).

        The upstream gateway is NOT local: it is the internet boundary, so
        traffic to/from it is internet (upload/download) traffic.
        """
        if ip is None:
            return False
        # Strip /32 or /24 suffix from INET type
        clean_ip = ip.split('/')[0]
        try:
            ip_addr = ipaddress.ip_address(clean_ip)

            # The gateway is the internet boundary, not a LAN device.
            if self.upstream_gateway is not None and ip_addr == self.upstream_gateway:
                return False

            # Check against configured LAN network (IPv4)
            if ip_addr in self.lan_network:
                return True
            # Also check for IPv6 link-local addresses (fe80::/10).
            # Link-local between the monitor and the gateway is still
            # boundary traffic, so treat link-local as external (non-local)
            # rather than consuming upload/download as LOCAL.
            if ip_addr.version == 6 and ip_addr.is_link_local:
                return False
            return False
        except ValueError:
            return False

    def _normalize_endpoint(
        self,
        ip,
        port,
    ):
        return f"{ip}:{port}"

    def _make_key(self, packet):

        endpoint_a = self._normalize_endpoint(
            packet["source_ip"],
            packet["source_port"],
        )

        endpoint_b = self._normalize_endpoint(
            packet["destination_ip"],
            packet["destination_port"],
        )

        endpoints = sorted(
            [endpoint_a, endpoint_b]
        )

        return (
            f"{endpoints[0]}"
            f"<->"
            f"{endpoints[1]}"
            f"/"
            f"{packet['protocol']}"
        )

    def _get_direction(self, packet):

        source_local = self._is_local(packet["source_ip"])
        destination_local = self._is_local(packet["destination_ip"])

        if source_local and not destination_local:
            return "UPLOAD"

        if not source_local and destination_local:
            return "DOWNLOAD"

        return "LOCAL"

    def process_packet(self, packet, device_id=None):

        key = self._make_key(packet)

        now = datetime.now(timezone.utc)
        
        direction = self._get_direction(packet)

        if key not in self.flows:

            self.flows[key] = Flow(
                key=key,

                source_ip=packet["source_ip"],
                destination_ip=packet["destination_ip"],

                source_port=packet["source_port"],
                destination_port=packet["destination_port"],

                protocol=packet["protocol"],

                interface=self.interface,
                
                direction=direction,

                started_at=now,
                last_seen=now,
                device_id=device_id,
            )

        flow = self.flows[key]

        flow.last_seen = now

        flow.packets += 1
        flow.bytes += packet["size"]

        if direction == "UPLOAD":

            flow.upload_bytes += packet["size"]

        elif direction == "DOWNLOAD":

            flow.download_bytes += packet["size"]
        
        # Store SNI if present in packet (from TLS Client Hello)
        if packet.get("sni") and not flow.sni:
            flow.sni = packet["sni"]
            
        # Update device_id if provided and not already set
        if device_id and not flow.device_id:
            flow.device_id = device_id

        return flow

    def cleanup(self):

        now = datetime.now(timezone.utc)

        closed = []
        keys_to_remove = []

        for key, flow in self.flows.items():

            elapsed = (
                now - flow.last_seen
            ).total_seconds()

            if elapsed > self.flow_timeout:

                flow.state = "CLOSED"

                closed.append(flow)
                keys_to_remove.append(key)

        # Remove closed flows from memory
        for key in keys_to_remove:
            del self.flows[key]

        return closed

    def get_active_flows(self):

        return [
            flow
            for flow in self.flows.values()
            if flow.state == "ACTIVE"
        ]