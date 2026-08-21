from analytics.protocols import (
    classify_protocol,
)

from analytics.applications import (
    detect_application,
)

from analytics.categories import (
    get_category,
)

from analytics.dns import DNSAnalyzer

from analytics.domains import (
    DomainAnalytics,
)


class AnalyticsEngine:

    def __init__(self):

        self.dns = DNSAnalyzer()

        self.domains = DomainAnalytics()

    def process_packet(
        self,
        packet,
    ):

        protocol = classify_protocol(
            packet.get("protocol", ""),
            packet.get("source_port"),
            packet.get("destination_port"),
        )

        packet["classified_protocol"] = (
            protocol
        )

        return packet

    def process_dns(
        self,
        device_ip,
        domain,
        query_type="A",
    ):

        self.dns.process_query(
            device_ip,
            domain,
            query_type,
        )

        self.domains.record_query(
            domain,
            device_ip,
        )

        application = detect_application(
            domain
        )

        category = get_category(
            application
        )

        return {
            "device_ip": device_ip,
            "domain": domain,
            "application": application,
            "category": category,
        }