from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface
from textwrap import dedent
from uuid import uuid4

from django.utils.text import slugify

from wireguard.models import WireguardClient
from wireguard.utils import format_network


def client_config(client: WireguardClient) -> str:
    conf = dedent(
        f"""\
        [connection]
        id={slugify(client.server.name)}
        uuid={str(uuid4())}
        type=wireguard
        interface-name={client.server.interface_name}

        [wireguard]
        private-key={client.private_key}

        [wireguard-peer.{client.server.public_key}]
        endpoint={client.server.hostname}:{client.server.port}
        """
    )

    if client.server.keepalive > 0 and client.keepalive == 0:
        conf += f"persistent-keepalive = {client.server.keepalive}\n"
    elif client.keepalive > 0:
        conf += f"persistent-keepalive = {client.keepalive}\n"

    # do we want to route everything?
    if client.server.is_exitnode and client.route_all_traffic:
        ips: list[str] = []
        conf += "allowed-ips="
        v4 = False
        v6 = False
        for network in client.server.networks.filter(is_client_network=True):
            i = network.interface
            if isinstance(i, IPv4Interface):
                v4 = True
            if isinstance(i, IPv6Interface):
                v6 = True
        if v4:
            ips.append("0.0.0.0/0")
        if v6:
            ips.append("::/0")
        conf += ";".join(ips) + ";\n"
    else:
        # only route vpn networks
        ips: list[str] = []
        for network in client.server.networks.all():
            ips.append(str(network.interface.network))
        conf += f"allowed-ips={';'.join(ips)};\n"

    confv4 = "[ipv4]\nmethod=manual\n"
    idxv4 = 1
    confv6 = "[ipv6]\nmethod=manual\n"
    idxv6 = 1

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
            if isinstance(client_ip, IPv4Address):
                confv4 += f"address{idxv4}={format_network(ip.ip, cidr=net.cidr_mask)}\n"
                idxv4 += 1
            if isinstance(client_ip, IPv6Address):
                confv6 += f"address{idxv6}={format_network(ip.ip, cidr=net.cidr_mask)}\n"
                idxv6 += 1

    if client.use_dns and client.server.has_dns:
        ipsv6: list[str] = []
        ipsv4: list[str] = []
        for network in client.server.networks.filter(is_client_network=True):
            if isinstance(network.interface, IPv4Interface):
                ipsv4.append(str(network.interface.ip))
            if isinstance(network.interface, IPv6Interface):
                ipsv6.append(str(network.interface.ip))
        confv4 += f"dns={';'.join(ipsv4)};\n"
        confv4 += f"dns-search={client.server.dns_domain};\n"
        confv6 += f"dns={';'.join(ipsv6)};\n"
        confv6 += f"dns-search={client.server.dns_domain};\n"

    conf += "\n" + confv4 + "\n" + confv6 + "\n"
    conf += "[proxy]\n"

    return conf
