from control.windows import run_powershell


class QoSController:

    PREFIX = "NetworkControl-QoS"

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

        else:

            raise ValueError(
                "Direction must be UPLOAD or DOWNLOAD"
            )

        run_powershell(command)

        return {
            "success": True,
            "device_id": device_id,
            "direction": direction,
            "limit_bps": bits_per_second,
        }