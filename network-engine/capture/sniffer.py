import threading
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
        self._stop_event = threading.Event()
        self._sniff_thread = None

    def _process_packet(self, packet):

        parsed = parse_packet(packet)

        if parsed is None:
            return

        self.callback(parsed)

    def _should_stop(self, packet):
        """Stop filter for scapy sniff"""
        return self._stop_event.is_set()

    def start(self):
        """Start packet capture in a separate thread"""
        self._stop_event.clear()
        self._sniff_thread = threading.Thread(
            target=self._sniff_loop,
            daemon=True,
            name="PacketSniffer"
        )
        self._sniff_thread.start()

    def _sniff_loop(self):
        """Run scapy sniff with stop filter.

        promisc=True so the monitor sees the phone's forwarded traffic even if
        the interface is not in promiscuous mode by default. In ICS topology the
        phone's packets still transit this interface (phone -> monitor Ethernet
        -> NAT -> Wi-Fi), so promiscuous mode is the robust choice and does not
        fabricate anything: it only widens what the adapter reports.
        """
        sniff(
            iface=self.interface,
            filter=self.capture_filter,
            prn=self._process_packet,
            store=False,
            stop_filter=self._should_stop,
            promisc=True,
        )

    def stop(self):
        """Stop packet capture gracefully"""
        self._stop_event.set()
        if self._sniff_thread and self._sniff_thread.is_alive():
            self._sniff_thread.join(timeout=5)
