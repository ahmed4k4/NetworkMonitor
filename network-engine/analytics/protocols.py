PORT_PROTOCOLS = {

    20: "FTP-DATA",
    21: "FTP",
    22: "SSH",
    23: "TELNET",

    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",

    80: "HTTP",
    110: "POP3",
    143: "IMAP",

    443: "HTTPS",

    465: "SMTPS",
    587: "SMTP",

    993: "IMAPS",
    995: "POP3S",

    3389: "RDP",

    5222: "XMPP",
}


def classify_protocol(
    protocol,
    source_port=None,
    destination_port=None,
):

    protocol = protocol.upper()

    if protocol == "ICMP":
        return "ICMP"

    ports = {
        source_port,
        destination_port,
    }

    for port in ports:

        if port in PORT_PROTOCOLS:

            return PORT_PROTOCOLS[port]

    if protocol == "TCP":
        return "TCP"

    if protocol == "UDP":

        if 53 in ports:
            return "DNS"

        if 443 in ports:
            return "QUIC"

        return "UDP"

    return protocol