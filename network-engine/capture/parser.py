from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Ether
from scapy.layers.tls.all import TLS, TLSClientHello, TLS_Ext_ServerName
from scapy.layers.dns import DNS, DNSQR
import ipaddress


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


def extract_sni(packet):
    """Extract SNI from TLS Client Hello packet"""
    try:
        if TLS in packet:
            tls_layer = packet[TLS]
            # Check if it's a Client Hello
            if TLSClientHello in packet:
                client_hello = packet[TLSClientHello]
                # Look for server_name extension
                for ext in client_hello.extensions:
                    if isinstance(ext, TLS_Ext_ServerName):
                        for server_name in ext.servernames:
                            return server_name.servername.decode('utf-8')
    except Exception:
        pass
    return None


def extract_dns(packet):
    """Extract DNS queries AND responses from a packet.

    Returns:
        {
            "domain": the query name (from question section),
            "query_type": numeric qtype,
            "response_ip": the first A/AAAA answer IP for responses, else None,
        }
    """
    try:
        if DNS in packet:
            dns = packet[DNS]

            domain = None
            query_type = None
            if dns.qd:
                question = dns.qd
                domain = question.qname.decode(errors="ignore").rstrip(".")
                query_type = question.qtype

            if dns.qr == 0:
                # DNS query
                return {
                    "domain": domain,
                    "query_type": query_type,
                    "response_ip": None,
                }

            # DNS response: extract the first A/AAAA answer IP as evidence for
            # flow -> domain correlation later.
            response_ip = None
            if dns.an:
                for answer in dns.an:
                    try:
                        answer_type = getattr(answer, "type", None)
                        rdata = getattr(answer, "rdata", None)
                        if rdata is None:
                            continue
                        if answer_type in (1, 28):  # A / AAAA
                            if isinstance(rdata, bytes):
                                response_ip = ipaddress.ip_address(rdata).compressed
                            else:
                                raw = str(rdata).split("/")[0]
                                ip_obj = ipaddress.ip_address(raw)
                                response_ip = ip_obj.compressed
                            break
                    except Exception:
                        continue
            return {
                "domain": domain,
                "query_type": query_type,
                "response_ip": response_ip,
            }
    except Exception:
        pass
    return None


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

    # Extract MAC addresses from Ethernet layer
    source_mac = None
    destination_mac = None
    if Ether in packet:
        eth = packet[Ether]
        source_mac = eth.src.upper().replace("-", ":")
        destination_mac = eth.dst.upper().replace("-", ":")

    # Extract SNI if present
    sni = extract_sni(packet)

    # Extract DNS if present
    dns = extract_dns(packet)

    return {
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "source_port": source_port,
        "destination_port": destination_port,
        "protocol": protocol,
        "size": len(packet),
        "source_mac": source_mac,
        "destination_mac": destination_mac,
        "sni": sni,
        "dns": dns,
    }