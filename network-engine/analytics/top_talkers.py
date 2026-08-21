class TopTalkers:

    def top_devices(
        self,
        stats,
        limit=10,
    ):

        devices = []

        for ip, data in stats.items():

            devices.append(
                {
                    "ip": ip,
                    "upload": data["upload"],
                    "download": data["download"],
                    "total": data["total"],
                    "packets": data["packets"],
                }
            )

        return sorted(
            devices,
            key=lambda x: x["total"],
            reverse=True,
        )[:limit]