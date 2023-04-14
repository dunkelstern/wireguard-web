from ipaddress import IPv4Interface
from textwrap import dedent

from wireguard.models import WireguardClient
from wireguard.utils import format_network

from .wgquick import client_config


__all__ = ("netctl", "client_config")


def netctl(client: WireguardClient) -> str:
    conf = dedent(
        f"""\
        Description="WireGuard tunnel to {client.server.name}"
        Interface={client.server.interface_name}
        Connection=wireguard
        WGConfigFile=/etc/wireguard/{client.server.interface_name}.conf

        IP=static
        """
    )

    ips: list[str] = []
    for ip in client.ips.all():
        client_ip = ip.ip_address

        # fetch network mask from server definition
        net = None
        for network in client.server.networks.filter(is_client_network=True):
            if client_ip in network.interface.network:
                net = network
                break
        if net:
            ips.append("'" + format_network(ip.ip, cidr=net.cidr_mask) + "'")
    conf += f"Address=({' '.join(ips)})\n"

    if client.use_dns and client.server.has_dns:
        ips: list[str] = []
        for network in client.server.networks.filter(is_client_network=True):
            ips.append("'" + str(network.interface.ip) + "'")
        conf += f"DNS=({' '.join(ips)})\n"

    found = False
    for network in client.server.networks.all():
        if isinstance(network.interface, IPv4Interface) and not found:
            conf += f"Gateway={str(network.interface.ip)}\n"
            found = True
        else:
            conf += f"# Gateway={str(network.interface.ip)}\n"
    return conf
