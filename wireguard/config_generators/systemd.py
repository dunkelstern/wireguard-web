import socket
from ipaddress import IPv4Interface, IPv6Interface
from random import randint
from textwrap import dedent

from wireguard.models import WireguardClient
from wireguard.utils import format_network


def netdev(client: WireguardClient) -> str:
    conf = dedent(
        f"""\
        [NetDev]
        Name={client.server.interface_name}
        Kind=wireguard
        Description=Wireguard tunnel {client.server.interface_name} to {client.server.name}

        [WireGuard]
        ListenPort={randint(20000, 50000)}
        PrivateKey={client.private_key}
        """
    )

    if client.server.is_exitnode and client.route_all_traffic:
        conf += "FirewallMark=0x8888\n"

    conf += dedent(
        f"""
        [WireGuardPeer]
        # {client.server.name} @ {client.server.interface_name}
        PublicKey={client.server.public_key}
        """
    )

    if client.server.is_exitnode and client.route_all_traffic:
        v4 = False
        v6 = False
        for network in client.server.networks.filter(is_client_network=True):
            i = network.interface
            if isinstance(i, IPv4Interface):
                v4 = True
            if isinstance(i, IPv6Interface):
                v6 = True
        if v4:
            conf += "AllowedIPs=0.0.0.0/0\n"
        if v6:
            conf += "AllowedIPs=::/0\n"

        # resolve the endpoint to allow full VPN with DNS
        if client.use_dns and client.server.has_dns:
            addr = socket.getaddrinfo(client.server.hostname, client.server.port, proto=socket.IPPROTO_UDP)
            conf += "# As DNS will go through the tunnel, you cannot resolve the endpoint IP\n"
            conf += "# for that purpose we resolve it here for you\n"
            conf += f"# Endpoint={client.server.hostname}:{client.server.port}\n"
            found = False
            for family, typ, proto, canonname, sockaddr in addr:
                if family == socket.AF_INET:
                    endpoint = f"{sockaddr[0]}:{client.server.port}"
                else:
                    endpoint = f"[{sockaddr[0]}]:{client.server.port}"
                if family == socket.AF_INET and not found:
                    found = True
                    conf += f"Endpoint={endpoint}\n"
                else:
                    conf += f"# Endpoint={endpoint}\n"
        else:
            conf += f"Endpoint={client.server.hostname}:{client.server.port}\n"
    else:
        for network in client.server.networks.all():
            conf += f"AllowedIPs={network.interface.network}\n"
        conf += f"Endpoint={client.server.hostname}:{client.server.port}\n"

    if client.server.keepalive > 0 and client.keepalive == 0:
        conf += f"PersistentKeepalive={client.server.keepalive}"
    elif client.keepalive > 0:
        conf += f"PersistentKeepalive={client.keepalive}"

    return conf


def network(client: WireguardClient) -> str:
    conf = dedent(
        f"""\
        [Match]
        Name={client.server.interface_name}

        [Network]
        """
    )

    for ip in client.ips.all():
        client_ip = ip.ip_address

        # fetch network mask from server definition
        net = None
        for network in client.server.networks.filter(is_client_network=True):
            if client_ip in network.interface.network:
                net = network
                break
        if net:
            conf += f"Address={format_network(ip.ip, cidr=net.cidr_mask)}\n"

    if client.use_dns and client.server.has_dns:
        for network in client.server.networks.filter(is_client_network=True):
            conf += f"DNS={str(network.interface.ip)}\n"

        if client.server.is_exitnode and client.route_all_traffic:
            conf += "Domains=~.\n"
            conf += "DNSDefaultRoute=true\n"
        else:
            conf += f"Domains={client.server.dns_domain}\n"

    conf += "\n"

    if client.server.is_exitnode and client.route_all_traffic:
        network = client.server.networks.filter(is_client_network=True).first()

        conf += dedent(
            f"""\
            # If you want to exempt local LAN addresses from the VPN
            # use another RoutingPolicyRule like this:
            #
            # [RoutingPolicyRule]
            # To=192.168.0.0/24
            # Priority=9

            [RoutingPolicyRule]
            FirewallMark=0x8888
            InvertRule=true
            Table=1000
            Priority=10

            [Route]
            Gateway={network.interface.ip}
            GatewayOnLink=true
            Table=1000
            """
        )
    else:
        # only route vpn networks
        for network in client.server.networks.all():
            conf += "[Route]\n"
            conf += f"Destination={str(network.interface.network)}\n"
            conf += "Scope=link\n"
            conf += "\n"

    return conf
