from datetime import datetime

from models.flow import Flow


class FlowManager:

    def __init__(
        self,
        network,
        interface,
        flow_timeout=60,
    ):
        self.network = network
        self.interface = interface
        self.flow_timeout = flow_timeout

        self.flows = {}

    def _is_local(self, ip: str) -> bool:
        """Check if IP is in the LAN network (handles /32 suffix)"""
        if ip is None:
            return False
        # Strip /32 or /24 suffix from INET type
        clean_ip = ip.split('/')[0]
        return clean_ip.startswith("192.168.137.")

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

        source_local = self._is_local(
            packet["source_ip"]
        )

        destination_local = self._is_local(
            packet["destination_ip"]
        )

        if source_local and not destination_local:
            return "UPLOAD"

        if not source_local and destination_local:
            return "DOWNLOAD"

        return "LOCAL"

    def process_packet(self, packet):

        key = self._make_key(packet)

        now = datetime.now()
        
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
            )

        flow = self.flows[key]

        flow.last_seen = now

        flow.packets += 1
        flow.bytes += packet["size"]

        if direction == "UPLOAD":

            flow.upload_bytes += packet["size"]

        elif direction == "DOWNLOAD":

            flow.download_bytes += packet["size"]

        return flow

    def cleanup(self):

        now = datetime.now()

        closed = []

        for key, flow in self.flows.items():

            elapsed = (
                now - flow.last_seen
            ).total_seconds()

            if elapsed > self.flow_timeout:

                flow.state = "CLOSED"

                closed.append(flow)

        return closed

    def get_active_flows(self):

        return [
            flow
            for flow in self.flows.values()
            if flow.state == "ACTIVE"
        ]