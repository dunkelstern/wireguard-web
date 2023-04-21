import re
from ipaddress import IPv4Address, IPv6Address

from django.core.exceptions import ValidationError
from django.db import models


DOMAIN_REGEX = re.compile(
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?))", flags=re.IGNORECASE
)


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

    server = models.ForeignKey(
        "wireguard.WireguardServer", on_delete=models.CASCADE, null=False, blank=False, related_name="dns"
    )

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
