from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Union

from django.db import models


class WireguardClientIP(models.Model):
    ip = models.GenericIPAddressField(
        "IP Address", unpack_ipv4=True, help_text="This defines an IP address the client will be assigned by wireguard"
    )
    client = models.ForeignKey(
        "wireguard.WireguardClient", on_delete=models.CASCADE, null=False, blank=False, related_name="ips"
    )

    class Meta:
        verbose_name = "IP Address"
        verbose_name_plural = "IP Addresses"

    def save(self, *args, **kwargs):
        # TODO: Make sure we do not collide with any other client on the same network
        super().save(*args, **kwargs)

    @property
    def ip_address(self) -> Union[IPv4Address, IPv6Address]:
        return ip_address(self.ip)

    @property
    def is_ipv4(self) -> bool:
        return isinstance(self.ip_address, IPv4Address)

    @property
    def is_ipv6(self) -> bool:
        return isinstance(self.ip_address, IPv6Address)

    def __str__(self) -> str:
        return f"{self.ip}"
