from django.utils.text import slugify

from wireguard.models import WireguardServer, WireguardServerDNSOverrides


def dns_config(server: WireguardServer) -> str:
    config = f"# dnsmasq.conf for {server.name} @ {server.interface_name}\n\nbind-interfaces\n"

    for network in server.networks.filter(is_client_network=True):
        config += f"listen-address={network.interface.ip}\n"
        config += f"no-dhcp-interface={network.interface.ip}\n"

    config += "\n# DNS for gateway\n"
    for network in server.networks.all():
        # add server name
        config += f"address=/{slugify(server.name)}.{server.dns_domain}/{network.interface.ip}\n"

    if server.clients_may_communicate:
        config += "\n# DNS for clients\n"
        for client in server.clients.all():
            for ip in client.ips.all():
                config += f"address=/{client.dns_name}/{ip.ip}\n"

    # add dns overrides
    if server.dns.count() > 0:
        config += "\n# DNS overrides\n"
    for dns in server.dns.all():
        if dns.type == WireguardServerDNSOverrides.DNSEntryType.A:
            config += f"address=/{dns.domain}/{dns.value}\n"
        elif dns.type == WireguardServerDNSOverrides.DNSEntryType.AAAA:
            config += f"address=/{dns.domain}/{dns.value}\n"
        elif dns.type == WireguardServerDNSOverrides.DNSEntryType.CNAME:
            config += f"cname={dns.domain},{dns.value}\n"
        elif dns.type == WireguardServerDNSOverrides.DNSEntryType.MX:
            config += f"mx-host={dns.domain},{dns.value},100\n"
        elif dns.type == WireguardServerDNSOverrides.DNSEntryType.TXT:
            config += f'txt-record={dns.domain},"{dns.value}"\n'
        elif dns.type == WireguardServerDNSOverrides.DNSEntryType.SRV:
            config += f"srv-host={dns.domain},{dns.value}\n"

    return config
