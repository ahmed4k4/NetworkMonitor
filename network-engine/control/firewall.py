import re
from control.windows import run_powershell


class FirewallController:

    # ...

    def _validate_device_id(self, device_id: str) -> str:
        """Validate and sanitize device_id to prevent injection"""
        # Device ID should be alphanumeric with hyphens/underscores only
        if not re.match(r'^[a-zA-Z0-9_-]+$', device_id):
            raise ValueError(f"Invalid device_id: {device_id}")
        return device_id

    def _validate_ip(self, ip: str) -> str:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

    def block_device(
        self,
        device_id: str,
        ip: str,
    ):

        # Validate inputs
        device_id = self._validate_device_id(device_id)
        ip = self._validate_ip(ip)

        inbound = (
            f"NetworkControl-Block-"
            f"{device_id}-IN"
        )

        outbound = (
            f"NetworkControl-Block-"
            f"{device_id}-OUT"
        )

        command = f"""
        Remove-NetFirewallRule `
            -DisplayName '{inbound}' `
            -ErrorAction SilentlyContinue

        Remove-NetFirewallRule `
            -DisplayName '{outbound}' `
            -ErrorAction SilentlyContinue

        New-NetFirewallRule `
            -DisplayName '{inbound}' `
            -Direction Inbound `
            -Action Block `
            -RemoteAddress '{ip}' `
            -Profile Any

        New-NetFirewallRule `
            -DisplayName '{outbound}' `
            -Direction Outbound `
            -Action Block `
            -RemoteAddress '{ip}' `
            -Profile Any
        """

        run_powershell(command)

        return {
            "success": True,
            "action": "block",
        }

    def unblock_device(
        self,
        device_id: str,
    ):

        # Validate input
        device_id = self._validate_device_id(device_id)

        command = f"""
        Remove-NetFirewallRule `
            -DisplayName 'NetworkControl-Block-{device_id}-IN' `
            -ErrorAction SilentlyContinue

        Remove-NetFirewallRule `
            -DisplayName 'NetworkControl-Block-{device_id}-OUT' `
            -ErrorAction SilentlyContinue
        """

        run_powershell(command)

        return {
            "success": True,
            "action": "unblock",
        }

    def pause_device(
        self,
        device_id: str,
        ip: str,
    ):

        # Validate inputs
        device_id = self._validate_device_id(device_id)
        ip = self._validate_ip(ip)

        inbound = (
            f"NetworkControl-Pause-"
            f"{device_id}-IN"
        )

        outbound = (
            f"NetworkControl-Pause-"
            f"{device_id}-OUT"
        )

        command = f"""
        Remove-NetFirewallRule `
            -DisplayName '{inbound}' `
            -ErrorAction SilentlyContinue

        Remove-NetFirewallRule `
            -DisplayName '{outbound}' `
            -ErrorAction SilentlyContinue

        New-NetFirewallRule `
            -DisplayName '{inbound}' `
            -Direction Inbound `
            -Action Block `
            -RemoteAddress '{ip}' `
            -Profile Any

        New-NetFirewallRule `
            -DisplayName '{outbound}' `
            -Direction Outbound `
            -RemoteAddress '{ip}' `
            -Action Block `
            -Profile Any
        """

        run_powershell(command)

        return {
            "success": True,
            "action": "pause",
        }

    def resume_device(
        self,
        device_id: str,
    ):

        # Validate input
        device_id = self._validate_device_id(device_id)

        command = f"""
        Remove-NetFirewallRule `
            -DisplayName 'NetworkControl-Pause-{device_id}-IN' `
            -ErrorAction SilentlyContinue

        Remove-NetFirewallRule `
            -DisplayName 'NetworkControl-Pause-{device_id}-OUT' `
            -ErrorAction SilentlyContinue
        """

        run_powershell(command)

        return {
            "success": True,
            "action": "resume",
        }
