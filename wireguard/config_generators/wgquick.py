from ipaddress import IPv4Interface, IPv6Interface
from textwrap import dedent

from wireguard.models import WireguardClient, WireguardServer
from wireguard.utils import format_network


def server_config(server: WireguardServer) -> str:
    interface = dedent(
        f"""\
        [Interface]
        # {server.name} @ {server.interface_name}
        PrivateKey = {server.private_key}
        ListenPort = {server.port}
        """
    )
    if server.fw_mark:
        interface += f"FwMark = {server.fw_mark}\n"

    ips: list[str] = []
    for network in server.networks.all():
        ips.append(format_network(network.ip, cidr=network.cidr_mask))
    interface += f"Address = {','.join(ips)}\n"

    # if we are an exit node, add nat routing
    if server.is_exitnode:
        interface += "PostUp = iptables -A FORWARD -i %i -j ACCEPT;"
        interface += f"iptables -t nat -A POSTROUTING -o {server.exit_interface} -j MASQUERADE\n"
        interface += "PostDown = iptables -D FORWARD -i %i -j ACCEPT;"
        interface += f"iptables -t nat -D POSTROUTING -o {server.exit_interface} -j MASQUERADE\n"

    # finally add peers
    peers: list[str] = []
    for peer in WireguardClient.objects.filter(server=server):
        conf = dedent(
            f"""
            [Peer]
            # {peer.name}
            PublicKey = {peer.public_key}
            """
        )
        if peer.preshared_key:
            conf += f"PresharedKey = {peer.preshared_key}\n"
        if peer.keepalive:
            conf += f"PersistentKeepalive = {peer.keepalive}\n"
        ips: list[str] = []
        for ip in peer.ips.all():
            ips.append(format_network(ip.ip))
        if peer.is_exitnode:
            for ip in peer.networks.all():
                ips.append(format_network(ip.ip, cidr=ip.cidr_mask))
        conf += f"AllowedIPs = {','.join(ips)}"
        peers.append(conf)

    return "\n".join([interface, *peers])


def client_config(client: WireguardClient) -> str:
    interface = dedent(
        f"""\
        [Interface]
        # {client.name}
        PrivateKey = {client.private_key}
        """
    )

    if client.use_dns and client.server.has_dns:
        ips: list[str] = []
        for network in client.server.networks.filter(is_client_network=True):
            ips.append(str(network.interface.ip))
        interface += f"DNS = {','.join(ips)}\n"

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
            ips.append(format_network(ip.ip, cidr=net.cidr_mask))
    interface += f"Address = {','.join(ips)}\n"

    # if we are an exit node, add nat routing
    if client.is_exitnode:
        interface += "PostUp = iptables -A FORWARD -i %i -j ACCEPT;"
        interface += f"iptables -t nat -A POSTROUTING -o {client.exit_interface} -j MASQUERADE\n"
        interface += "PostDown = iptables -D FORWARD -i %i -j ACCEPT;"
        interface += f"iptables -t nat -D POSTROUTING -o {client.exit_interface} -j MASQUERADE\n"

    conf = dedent(
        f"""
        [Peer]
        # {client.server.name} @ {client.server.interface_name}
        PublicKey = {client.server.public_key}
        """
    )

    # do we want to route everything?
    if client.server.is_exitnode and client.route_all_traffic:
        ips: list[str] = []
        conf += "AllowedIPs = "
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
        conf += ",".join(ips) + "\n"

    else:
        # only route vpn networks
        ips: list[str] = []
        for network in client.server.networks.all():
            ips.append(str(network.interface.network))
        conf += f"AllowedIPs = {','.join(ips)}\n"

    conf += f"Endpoint = {client.server.hostname}:{client.server.port}\n"

    if client.server.keepalive > 0 and client.keepalive == 0:
        conf += f"PersistentKeepalive = {client.server.keepalive}"
    elif client.keepalive > 0:
        conf += f"PersistentKeepalive = {client.keepalive}"

    return "\n".join([interface, conf])
