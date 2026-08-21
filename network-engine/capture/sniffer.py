from scapy.all import sniff

from .parser import parse_packet


class PacketSniffer:

    def __init__(
        self,
        interface,
        callback,
        capture_filter="",
    ):
        self.interface = interface
        self.callback = callback
        self.capture_filter = capture_filter

    def _process_packet(self, packet):

        parsed = parse_packet(packet)

        if parsed is None:
            return

        self.callback(parsed)

    def start(self):

        sniff(
            iface=self.interface,
            filter=self.capture_filter,
            prn=self._process_packet,
            store=False,
        )

    def stop(self):
        pass