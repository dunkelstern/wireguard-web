import random
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_interface
from typing import Optional, Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from wireguard.signals import update_config
from wireguard.utils import endpoint, format_network, gen_key, last_handshake, public_key_from_private

from .ip import WireguardClientIP


class WireguardClient(models.Model):
    name = models.CharField(
        "Client name",
        max_length=128,
        null=False,
        blank=False,
        unique=True,
        help_text="The client name to identify this device. This becomes the DNS name",
    )

    private_key = models.CharField("Private key", max_length=128, null=False, blank=True)
    public_key = models.CharField("Public key", max_length=128, null=False, blank=True)
    keepalive = models.IntegerField("Keepalive timeout", null=False, default=0)

    use_dns = models.BooleanField(
        "Use server DNS",
        default=False,
        help_text="Select this to use the VPN's DNS server. If you're routing all traffic through this server, "
        "all DNS queries will go through the server too. If not all traffic is routed through the DNS "
        "the implementation on the clients differ, but optimally they will only send queries for the "
        "DNS domain.",
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=False)
    server = models.ForeignKey("wireguard.WireguardServer", on_delete=models.PROTECT, related_name="clients")
    route_all_traffic = models.BooleanField(
        "Route all traffic",
        default=False,
        help_text="Directs the client to route all traffic through this VPN, be aware that this might break local "
        "access to the network.",
    )
    is_exitnode = models.BooleanField(
        "Exitnode", default=False, help_text="This client is a NAT gateway/exit node to a bridged network"
    )
    exit_interface = models.CharField(
        "Exit interface",
        max_length=16,
        null=True,
        blank=True,
        default=None,
        help_text="Network interface to which to route external traffic",
    )
    allow_direct_peering = models.BooleanField(
        "Allow P2P target",
        default=False,
        help_text="Allow direct communication with this client by other clients in the same network without "
        "bouncing traffic over the VPN server",
    )

    class Meta:
        unique_together = ("server", "name")
        ordering = ("server", "name")

    @property
    def dns_name(self) -> Optional[str]:
        """If the server has DNS this returns the DNS name of this client"""
        if self.server.has_dns:
            return f"{slugify(self.name)}.{self.server.dns_domain}"
        return None

    @property
    def endpoint(self) -> Optional[str]:
        """This returns the connected endpoint's IP Address"""
        result = endpoint(self.public_key)
        if result:
            return ":".join(result.rsplit(":")[:-1])
        return None

    @property
    def port(self) -> Optional[int]:
        result = endpoint(self.public_key)
        if result:
            try:
                return int(result.rsplit(":")[-1])
            except ValueError:
                return None
        return None

    @property
    def last_handshake(self) -> datetime:
        return last_handshake(self.public_key)

    def clean(self, *args, **kwargs):
        if self.is_exitnode and (self.exit_interface == "" or self.exit_interface is None):
            raise ValidationError(
                {
                    "exit_interface": "If this is an exit node, you have to specify the exit "
                    "interface over which to route external traffic"
                }
            )
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs) -> None:
        # generate new private key
        if not self.private_key:
            self.private_key = gen_key()
            self.public_key = public_key_from_private(self.private_key)

        if self.server.keepalive:
            self.keepalive = self.server.keepalive

        result = super().save(*args, **kwargs)

        # add ip addresses
        if not self.pk or self.ips.count() == 0:
            # fetch all clients on this server
            addresses: list[Union[IPv4Address, IPv6Address]] = []
            for client in self.server.clients.all():
                for ip in client.ips.all():
                    addresses.append(ip.ip_address)

            # fetch the server ip networks and create an ip address in all of them
            for network in self.server.networks.filter(is_client_network=True):
                interface = ip_interface(format_network(network.ip, cidr=network.cidr_mask))
                net = interface.network.network_address
                while True:
                    # generate new random ip
                    ip = net + random.randint(1, interface.network.num_addresses)
                    addr = ip_address(ip)

                    # check for collisions
                    if addr not in addresses:
                        break
                # add the ip to our client
                self.ips.add(WireguardClientIP(ip=str(addr)), bulk=False)

        update_config.send(self.__class__, server=self.server)
        return result

    def __str__(self) -> str:
        return f"{self.name}@{self.server}"
