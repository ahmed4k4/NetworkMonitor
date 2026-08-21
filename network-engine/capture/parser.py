from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6


def get_protocol(packet):

    if TCP in packet:
        return "TCP"

    if UDP in packet:
        return "UDP"

    if ICMP in packet:
        return "ICMP"

    if IP in packet:
        return "IP"

    if IPv6 in packet:
        return "IPv6"

    return "OTHER"


def parse_packet(packet):

    if IP in packet:

        ip_layer = packet[IP]

        source_ip = ip_layer.src
        destination_ip = ip_layer.dst

    elif IPv6 in packet:

        ip_layer = packet[IPv6]

        source_ip = ip_layer.src
        destination_ip = ip_layer.dst

    else:
        return None

    source_port = None
    destination_port = None

    if TCP in packet:

        source_port = packet[TCP].sport
        destination_port = packet[TCP].dport

    elif UDP in packet:

        source_port = packet[UDP].sport
        destination_port = packet[UDP].dport

    protocol = get_protocol(packet)

    return {
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "source_port": source_port,
        "destination_port": destination_port,
        "protocol": protocol,
        "size": len(packet),
    }