from scapy.layers.dns import DNS, DNSQR

def parse_dns(packet):

    if not packet.haslayer(DNS):
        return None

    dns = packet[DNS]

    if not dns.qd:
        return None

    query = dns.qd

    domain = query.qname.decode(
        errors="ignore"
    ).rstrip(".")

    return {
        "domain": domain,
        "query_type": query.qtype,
    }

class DNSAnalyzer:

    def __init__(self):

        self.queries = {}

    def process_query(
        self,
        device_ip,
        domain,
        query_type="A",
    ):

        key = (
            device_ip,
            domain,
            query_type,
        )

        if key not in self.queries:

            self.queries[key] = {
                "device_ip": device_ip,
                "domain": domain,
                "query_type": query_type,
                "count": 0,
            }

        self.queries[key]["count"] += 1

        return self.queries[key]

    def get_top_domains(
        self,
        limit=20,
    ):

        return sorted(
            self.queries.values(),
            key=lambda x: x["count"],
            reverse=True,
        )[:limit]