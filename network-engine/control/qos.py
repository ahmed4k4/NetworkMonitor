import re
import ipaddress
from control.windows import run_powershell


class QoSController:

    PREFIX = "NetworkControl-QoS"

    def _validate_device_id(self, device_id: str) -> str:
        """Validate and sanitize device_id to prevent injection"""
        # Device ID should be alphanumeric with hyphens/underscores only
        if not re.match(r'^[a-zA-Z0-9_-]+$', device_id):
            raise ValueError(f"Invalid device_id: {device_id}")
        return device_id

    def _validate_ip(self, ip: str) -> str:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

    def _validate_direction(self, direction: str) -> str:
        """Validate direction"""
        if direction not in ("UPLOAD", "DOWNLOAD"):
            raise ValueError("Direction must be UPLOAD or DOWNLOAD")
        return direction

    def _policy_name(
        self,
        device_id: str,
        direction: str,
    ) -> str:

        return (
            f"{self.PREFIX}-"
            f"{device_id}-"
            f"{direction}"
        )

    def remove_policy(
        self,
        device_id: str,
        direction: str,
    ):

        device_id = self._validate_device_id(device_id)
        direction = self._validate_direction(direction)

        name = self._policy_name(
            device_id,
            direction,
        )

        command = f"""
        Remove-NetQosPolicy `
            -Name '{name}' `
            -Confirm:$false `
            -ErrorAction SilentlyContinue
        """

        run_powershell(command)

    def set_limit(
        self,
        device_id: str,
        ip: str,
        direction: str,
        bits_per_second: int,
    ):

        device_id = self._validate_device_id(device_id)
        ip = self._validate_ip(ip)
        direction = self._validate_direction(direction)

        # Validate bits_per_second is a positive integer
        if not isinstance(bits_per_second, int) or bits_per_second <= 0:
            raise ValueError("bits_per_second must be a positive integer")

        name = self._policy_name(
            device_id,
            direction,
        )

        self.remove_policy(
            device_id,
            direction,
        )

        if direction == "UPLOAD":

            command = f"""
            New-NetQosPolicy `
                -Name '{name}' `
                -IPSrcPrefixMatchCondition '{ip}/32' `
                -ThrottleRateActionBitsPerSecond {bits_per_second}
            """

        elif direction == "DOWNLOAD":

            command = f"""
            New-NetQosPolicy `
                -Name '{name}' `
                -IPDstPrefixMatchCondition '{ip}/32' `
                -ThrottleRateActionBitsPerSecond {bits_per_second}
            """

        run_powershell(command)

        return {
            "success": True,
            "device_id": device_id,
            "direction": direction,
            "limit_bps": bits_per_second,
        }
