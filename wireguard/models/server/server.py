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
    allow_direct_peering = models.BooleanField("Allow client peer2peer communication", default=True)

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
