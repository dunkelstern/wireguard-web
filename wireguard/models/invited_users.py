from django.conf import settings
from django.db import models


class ServerAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False)
    server = models.ForeignKey(
        "wireguard.WireguardServer", on_delete=models.CASCADE, null=False, blank=False, related_name="invites"
    )
    created_at = models.DateField(auto_now_add=True, null=False, blank=True)

    class Meta:
        unique_together = ("user", "server")
        verbose_name = "Server Access"
        verbose_name_plural = "Server Access"
