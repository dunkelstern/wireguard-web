from ipaddress import IPv4Interface, IPv6Interface, ip_interface
from typing import Union

from django.db import models

from wireguard.utils import format_network


class WireguardServerNetworks(models.Model):
    ip = models.GenericIPAddressField("IP Address of server in Network", unpack_ipv4=True)
    cidr_mask = models.IntegerField(
        "If set, automatically update the client's allowed IPs to route to this net",
        null=True,
        default=None,
        blank=True,
    )
    server = models.ForeignKey(
        "wireguard.WireguardServer", on_delete=models.CASCADE, null=False, blank=False, related_name="networks"
    )
    is_client_network = models.BooleanField("Clients will get IPs from this network", default=False)

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
