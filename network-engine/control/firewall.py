from control.windows import run_powershell


class FirewallController:

    # ...

    def pause_device(
        self,
        device_id: str,
        ip: str,
    ):

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