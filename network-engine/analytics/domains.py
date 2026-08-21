from collections import defaultdict


class DomainAnalytics:

    def __init__(self):

        self.domains = defaultdict(
            lambda: {
                "queries": 0,
                "devices": set(),
                "bytes": 0,
            }
        )

    def record_query(
        self,
        domain,
        device_ip,
    ):

        data = self.domains[domain]

        data["queries"] += 1

        data["devices"].add(
            device_ip
        )

    def record_traffic(
        self,
        domain,
        bytes_count,
    ):

        self.domains[domain]["bytes"] += (
            bytes_count
        )

    def top_domains(
        self,
        limit=20,
    ):

        result = []

        for domain, data in self.domains.items():

            result.append(
                {
                    "domain": domain,
                    "queries": data["queries"],
                    "devices": len(
                        data["devices"]
                    ),
                    "bytes": data["bytes"],
                }
            )

        return sorted(
            result,
            key=lambda x: x["bytes"],
            reverse=True,
        )[:limit]