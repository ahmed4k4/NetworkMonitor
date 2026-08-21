import subprocess


class WindowsCommandError(Exception):
    pass


def run_powershell(
    command: str,
) -> str:

    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
    )

    if process.returncode != 0:

        raise WindowsCommandError(
            process.stderr.strip()
        )

    return process.stdout.strip()