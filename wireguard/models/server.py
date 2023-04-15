import re
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface, ip_interface
from typing import Union

from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet

from wireguard.signals import update_config
from wireguard.utils import format_network, gen_key, public_key_from_private


DOMAIN_REGEX = re.compile(
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?))", flags=re.IGNORECASE
)


class ServerManager(models.Manager):
    def allowed_servers_for_user(self, user: AbstractBaseUser) -> QuerySet:
        _, domain = user.email.rsplit("@")
        if user.is_superuser:
            return self.all()
        else:
            return self.filter(Q(self_registrations__email_domain=domain) | Q(invites__user=user))


class WireguardServer(models.Model):
    name = models.CharField("Server name", max_length=128, null=False, blank=False, unique=True)
    interface_name = models.CharField("Network interface name", max_length=16, null=False, blank=False, unique=True)
    hostname = models.CharField("Server host-name or IP", max_length=128, null=False, blank=False)
    enabled = models.BooleanField("Enable this server", null=False, blank=False, default=True)

    private_key = models.CharField("Private key", max_length=128, null=False, blank=True)
    port = models.IntegerField("Listening port", null=False, default=44000)
    fw_mark = models.IntegerField("FWMark for outgoing packets", null=False, default=0)
    keepalive = models.IntegerField("Persistent keepalive timeout", null=False, default=0)

    has_dns = models.BooleanField("This server has a DNS resolver", default=False)
    dns_domain = models.CharField(
        "Domain name for all clients when DNS is enabled", max_length=128, default="vpn.local"
    )
    is_exitnode = models.BooleanField("This server is a NAT gateway/exit node", default=False)
    exit_interface = models.CharField(
        "Network interface to which to route external traffic", max_length=16, null=True, blank=True, default=None
    )
    clients_may_communicate = models.BooleanField("Clients may communicate with each other", default=True)
    may_route_all_traffic = models.BooleanField("Clients may access the Internet through this server", default=False)
    allow_client_bridges = models.BooleanField("Clients may bridge to their Network", default=False)

    objects = ServerManager()

    class Meta:
        ordering = ("name", "interface_name", "enabled")

    @property
    def public_key(self) -> str:
        """This returns the public key that belongs to the stored private key"""
        return public_key_from_private(self.private_key)

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
        if not self.private_key:
            self.private_key = gen_key()
        result = super().save(*args, **kwargs)
        update_config.send(self.__class__, server=self)

        return result

    def __str__(self) -> str:
        return f"{self.name}:{self.port}"


class WireguardServerNetworks(models.Model):
    ip = models.GenericIPAddressField("IP Address of server in Network", unpack_ipv4=True)
    cidr_mask = models.IntegerField(
        "If set, automatically update the client's allowed IPs to route to this net",
        null=True,
        default=None,
        blank=True,
    )
    server = models.ForeignKey(
        WireguardServer, on_delete=models.CASCADE, null=False, blank=False, related_name="networks"
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


class WireguardServerSelfRegistration(models.Model):
    email_domain = models.CharField(
        "Users with this e-mail domain may self-register on this Server", max_length=128, null=False, blank=False
    )
    server = models.ForeignKey(
        WireguardServer, on_delete=models.CASCADE, null=False, blank=False, related_name="self_registrations"
    )

    class Meta:
        verbose_name = "Self Registration"
        verbose_name_plural = "Self Registrations"

    def __str__(self) -> str:
        return f"{self.email_domain}@{self.server}"


class WireguardServerDNSOverrides(models.Model):
    class DNSEntryType(models.TextChoices):
        A = "A", "IPv4 address record (A)"
        AAAA = "AAAA", "IPv6 address record (AAAA)"
        CNAME = "CNAME", "Domain Alias (CNAME)"
        MX = "MX", "Mail Server (MX)"
        TXT = "TXT", "Text Record (TXT)"
        SRV = "SRV", "Service Record (SRV)"

    domain = models.CharField("Domain name", max_length=255, blank=False, null=False)
    type = models.CharField("DNS entry type", max_length=32, choices=DNSEntryType.choices, default=DNSEntryType.A)
    value = models.CharField("Record value", max_length=1024, blank=True, null=False, default="")

    server = models.ForeignKey(WireguardServer, on_delete=models.CASCADE, null=False, blank=False, related_name="dns")

    class Meta:
        verbose_name = "DNS Override"
        verbose_name_plural = "DNS Overrides"
        unique_together = (
            (
                "domain",
                "type",
                "server",
            ),
        )

    def clean(self, *args, **kwargs):
        if not DOMAIN_REGEX.match(self.domain):
            raise ValidationError({"domain": "Please enter a valid domain name!"})
        if self.type == WireguardServerDNSOverrides.DNSEntryType.A:
            try:
                IPv4Address(self.value)
            except ValueError:
                raise ValidationError(
                    {"value": "Enter a valid IPv4 address."}, code="invalid", params={"value": self.value}
                )
        elif self.type == WireguardServerDNSOverrides.DNSEntryType.AAAA:
            try:
                IPv6Address(self.value)
            except ValueError:
                raise ValidationError(
                    {"value": "Enter a valid IPv6 address."}, code="invalid", params={"value": self.value}
                )
        elif (
            self.type == WireguardServerDNSOverrides.DNSEntryType.CNAME
            or self.type == WireguardServerDNSOverrides.DNSEntryType.MX
        ):
            if not DOMAIN_REGEX.match(self.value):
                raise ValidationError({"value": "Please enter a valid domain name!"})

        super().clean(*args, **kwargs)
