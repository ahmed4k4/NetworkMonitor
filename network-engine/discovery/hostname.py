import socket


def resolve_hostname(ip: str):

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname

    except (socket.herror, socket.gaierror, socket.timeout):
        return None