from ipaddress import IPv4Interface, IPv6Interface, ip_interface
from typing import Union

from django.db import models

from wireguard.utils import format_network


class WireguardServerNetworks(models.Model):
    ip = models.GenericIPAddressField(
        "IP Address", unpack_ipv4=True, help_text="IP address of the server in this network"
    )
    cidr_mask = models.IntegerField(
        "Netmask",
        null=True,
        default=None,
        blank=True,
        help_text="If this is set to a non-blank value it defines this is a network address and clients will "
        " get a route for this network",
    )
    server = models.ForeignKey(
        "wireguard.WireguardServer", on_delete=models.CASCADE, null=False, blank=False, related_name="networks"
    )
    is_client_network = models.BooleanField(
        "Client network", default=False, help_text="If set then clients will get random IPs from this network"
    )

    class Meta:
        verbose_name = "Network"
        verbose_name_plural = "Networks"

    @property
    def interface(self) -> Union[IPv4Interface, IPv6Interface]:
        return ip_interface(format_network(self.ip, cidr=self.cidr_mask))

    @property
    def is_ipv4(self) -> bool:
        return isinstance(self.interface, IPv4Interface)

    @property
    def is_ipv6(self) -> bool:
        return isinstance(self.interface, IPv6Interface)

    def __str__(self) -> str:
        return f"{self.ip}/{self.cidr_mask}"
