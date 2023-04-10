import random
from datetime import datetime
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface, ip_address, ip_interface

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from wireguard.signals import update_config
from wireguard.utils import endpoint, format_network, gen_key, last_handshake, public_key_from_private


class WireguardClient(models.Model):
    name = models.CharField("Client name", max_length=128, null=False, blank=False, unique=True)

    private_key = models.CharField("Private key", max_length=128, null=False, blank=True)
    preshared_key = models.CharField("Pre-Shared Key, optional", max_length=128, null=True, blank=True)
    keepalive = models.IntegerField("Persistent keepalive timeout", null=False, default=0)

    use_dns = models.BooleanField("Use the DNS of the server", default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=False)
    server = models.ForeignKey("wireguard.WireguardServer", on_delete=models.PROTECT, related_name="clients")
    route_all_traffic = models.BooleanField("Route all traffic through this Connection", default=False)
    is_exitnode = models.BooleanField("This client is a NAT gateway/exit node to a bridged network", default=False)
    exit_interface = models.CharField(
        "Network interface to which to route external traffic", max_length=16, null=True, blank=True, default=None
    )

    @property
    def public_key(self) -> str:
        """This returns the public key that belongs to the stored private key"""
        return public_key_from_private(self.private_key)

    @property
    def endpoint(self) -> str | None:
        """This returns the connected endpoint's IP Address"""
        result = endpoint(self.public_key)
        if result:
            return result.rsplit(":")[0]
        return None

    @property
    def port(self) -> int | None:
        result = endpoint(self.public_key)
        if result:
            return int(result.rsplit(":")[-1])
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

        if self.server.keepalive:
            self.keepalive = self.server.keepalive

        result = super().save(*args, **kwargs)

        # add ip addresses
        if not self.pk or self.ips.count() == 0:
            # fetch all clients on this server
            addresses: list[IPv4Address | IPv6Address] = []
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


class WireguardClientIP(models.Model):
    ip = models.GenericIPAddressField("IP Address of client in Network", unpack_ipv4=True)
    client = models.ForeignKey(WireguardClient, on_delete=models.CASCADE, null=False, blank=False, related_name="ips")

    class Meta:
        verbose_name = "IP Address"
        verbose_name_plural = "IP Addresses"

    def save(self, *args, **kwargs):
        # TODO: Make sure we do not collide with any other client on the same network
        super().save(*args, **kwargs)

    @property
    def ip_address(self) -> IPv4Address | IPv6Address:
        return ip_address(self.ip)

    @property
    def is_ipv4(self) -> bool:
        return isinstance(self.ip_address, IPv4Address)

    @property
    def is_ipv6(self) -> bool:
        return isinstance(self.ip_address, IPv6Address)

    def __str__(self) -> str:
        return f"{self.ip}"


class WireguardClientNetworks(models.Model):
    ip = models.GenericIPAddressField("IP Network", unpack_ipv4=True)
    cidr_mask = models.IntegerField(
        "Netmask in CIDR form for this network",
        null=False,
        blank=False,
    )
    client = models.ForeignKey(
        WireguardClient, on_delete=models.CASCADE, null=False, blank=False, related_name="networks"
    )

    class Meta:
        verbose_name = "Network"
        verbose_name_plural = "Networks"

    def __str__(self) -> str:
        return f"{self.ip}/{self.cidr_mask}"

    @property
    def interface(self) -> IPv4Interface | IPv6Interface:
        return ip_interface(format_network(self.ip, cidr=self.cidr_mask))

    @property
    def is_ipv4(self) -> bool:
        return isinstance(self.interface, IPv4Interface)

    @property
    def is_ipv6(self) -> bool:
        return isinstance(self.interface, IPv6Interface)
