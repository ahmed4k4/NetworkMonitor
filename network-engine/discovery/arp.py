from scapy.all import ARP, Ether, srp


def scan_network(network: str, interface: str):

    arp_request = ARP(pdst=network)

    ethernet_frame = Ether(
        dst="ff:ff:ff:ff:ff:ff"
    )

    packet = ethernet_frame / arp_request

    answered, _ = srp(
        packet,
        iface=interface,
        timeout=2,
        verbose=False,
    )

    devices = []

    for _, response in answered:

        devices.append(
            {
                "ip": response.psrc,
                "mac": response.hwsrc.upper(),
            }
        )

    return devices