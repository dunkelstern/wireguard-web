from ipaddress import IPv4Interface, IPv6Interface, ip_interface
from typing import Union

from django.db import models

from wireguard.utils import format_network


class WireguardClientLocalNetwork(models.Model):
    ip = models.GenericIPAddressField(
        "IP Address", unpack_ipv4=True, help_text="This defines the IP address the client has in it's local network"
    )
    cidr_mask = models.IntegerField(
        "Network mask (CIDR)",
        null=True,
        default=None,
        blank=False,
    )
    gateway = models.GenericIPAddressField(
        "Gateway IP", unpack_ipv4=True, help_text="The default Gateway the client has in it's local network"
    )
    public_ip = models.GenericIPAddressField(
        "Public IP",
        unpack_ipv4=True,
        help_text="The public IP address seen when this entry was created, if the client endpoint changes from "
        "this value the entry becomes invalid.",
    )
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
