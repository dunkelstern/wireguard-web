from ipaddress import IPv4Interface, IPv6Interface, ip_interface
from typing import Union

from django.db import models

from wireguard.utils import format_network


class WireguardClientNetworks(models.Model):
    ip = models.GenericIPAddressField("IP Network", unpack_ipv4=True)
    cidr_mask = models.IntegerField(
        "Netmask in CIDR form for this network",
        null=False,
        blank=False,
    )
    client = models.ForeignKey(
        "wireguard.WireguardClient", on_delete=models.CASCADE, null=False, blank=False, related_name="networks"
    )

    class Meta:
        verbose_name = "Bridged Network"
        verbose_name_plural = "Bridged Networks"

    def __str__(self) -> str:
        return f"{self.ip}/{self.cidr_mask}"

    @property
    def interface(self) -> Union[IPv4Interface, IPv6Interface]:
        return ip_interface(format_network(self.ip, cidr=self.cidr_mask))

    @property
    def is_ipv4(self) -> bool:
        return isinstance(self.interface, IPv4Interface)

    @property
    def is_ipv6(self) -> bool:
        return isinstance(self.interface, IPv6Interface)
