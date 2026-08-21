from control.firewall import FirewallController
from control.qos import QoSController
from control.quotas import QuotaEngine


class ControlEngine:

    def __init__(self):

        self.firewall = (
            FirewallController()
        )

        self.qos = (
            QoSController()
        )

        self.quotas = (
            QuotaEngine()
        )


    def block(
        self,
        device_id: str,
        ip: str,
    ):

        return self.firewall.block_device(
            device_id,
            ip,
        )


    def unblock(
        self,
        device_id: str,
    ):

        return self.firewall.unblock_device(
            device_id,
        )


    def pause(
        self,
        device_id: str,
        ip: str,
    ):

        return self.firewall.pause_device(
            device_id,
            ip,
        )


    def resume(
        self,
        device_id: str,
    ):

        return self.firewall.resume_device(
            device_id,
        )


    def limit(
        self,
        device_id: str,
        ip: str,
        download: int | None = None,
        upload: int | None = None,
    ):

        results = []

        if download is not None:

            results.append(
                self.qos.set_limit(
                    device_id,
                    ip,
                    "DOWNLOAD",
                    download,
                )
            )

        if upload is not None:

            results.append(
                self.qos.set_limit(
                    device_id,
                    ip,
                    "UPLOAD",
                    upload,
                )
            )

        return results