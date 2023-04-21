from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet

from wireguard.signals import update_config
from wireguard.utils import gen_key, public_key_from_private


class ServerManager(models.Manager):
    def allowed_servers_for_user(self, user: AbstractBaseUser) -> QuerySet:
        if user.is_superuser:
            return self.all()
        else:
            _, domain = user.email.rsplit("@")
            return self.filter(Q(self_registrations__email_domain=domain) | Q(invites__user=user)).distinct()


class WireguardServer(models.Model):
    name = models.CharField(
        "Server name",
        max_length=128,
        null=False,
        blank=False,
        unique=True,
        help_text="The server name to identify this VPN. This becomes the DNS name of the server",
    )
    interface_name = models.CharField(
        "Network interface",
        max_length=16,
        null=False,
        blank=False,
        unique=True,
        help_text="The interface name for this network, usual values are 'wg0' or 'wt0', but may be anything",
    )
    hostname = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        help_text="Server host-name or IP address on which this is reachable from the clients",
    )
    enabled = models.BooleanField("Enabled", null=False, blank=False, default=True)

    private_key = models.CharField("Private key", max_length=128, null=False, blank=True)
    port = models.IntegerField(
        "Listening port",
        null=False,
        default=44000,
        help_text="Port to listen on. If the server is behind a NAT please forward this UDP port. Use port > 1024",
    )
    fw_mark = models.IntegerField("FWMark", null=False, default=0)
    keepalive = models.IntegerField(
        "Keepalive timeout (seconds)",
        null=False,
        default=0,
        help_text="If this is set to a non-zero value this server enforces all clients to send keepalive messages",
    )

    has_dns = models.BooleanField(
        "DNS",
        default=False,
        help_text="This server should have a DNS resolver, an instance of dnsmasq is configured and started",
    )
    dns_domain = models.CharField(
        "DNS Domain", max_length=128, default="vpn.local", help_text="Domain name for all clients when DNS is enabled"
    )
    is_exitnode = models.BooleanField(
        "Exitnode",
        default=False,
        help_text="This server is a NAT gateway or exit node, if you enable routing all traffic through this "
        "server make sure the internet is accessible from the exit interface",
    )
    exit_interface = models.CharField(
        "NAT exit interface",
        max_length=16,
        null=True,
        blank=True,
        default=None,
        help_text="Network interface to which to route external traffic",
    )
    clients_may_communicate = models.BooleanField(
        "Client communication", default=True, help_text="Clients may communicate with each other and the VPN server"
    )
    may_route_all_traffic = models.BooleanField(
        "All traffic",
        default=False,
        help_text="Clients may access the Internet through this server by routing all IP traffic",
    )
    allow_client_bridges = models.BooleanField(
        "Client Bridges",
        default=False,
        help_text="Clients may bridge to their Network, be aware only staff users can configure their devices "
        "to allow bridges",
    )
    allow_direct_peering = models.BooleanField(
        "Client P2P", default=True, help_text="Allow client peer2peer communication"
    )

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
