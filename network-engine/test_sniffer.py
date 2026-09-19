import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from capture.sniffer import PacketSniffer
from capture.parser import parse_packet
import time

def test_callback(parsed):
    print('Packet:', parsed)
    if parsed.get('dns'):
        print('DNS found:', parsed['dns'])

sniffer = PacketSniffer('Ethernet', test_callback, capture_filter='udp port 53')
sniffer.start()
time.sleep(10)
sniffer.stop()