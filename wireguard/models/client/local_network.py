from ipaddress import IPv4Interface, IPv6Interface, ip_interface
from typing import Union

from django.db import models

from wireguard.utils import format_network


class WireguardClientLocalNetwork(models.Model):
    ip = models.GenericIPAddressField("IP Address", unpack_ipv4=True)
    cidr_mask = models.IntegerField(
        "Network mask (CIDR)",
        null=True,
        default=None,
        blank=False,
    )
    gateway = models.GenericIPAddressField("Gateway IP Address", unpack_ipv4=True)
    public_ip = models.GenericIPAddressField("Public IP Address", unpack_ipv4=True)
    client = models.ForeignKey(
        "wireguard.WireguardClient", on_delete=models.CASCADE, null=False, blank=False, related_name="local_networks"
    )

    class Meta:
        verbose_name = "Local Network"
        verbose_name_plural = "Local Networks"

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
