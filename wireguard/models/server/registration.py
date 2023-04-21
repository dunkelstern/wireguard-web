from django.db import models


class WireguardServerSelfRegistration(models.Model):
    email_domain = models.CharField(
        "e-Mail domain",
        max_length=128,
        null=False,
        blank=False,
        help_text="Users with this e-mail domain may self-register on this Server",
    )
    server = models.ForeignKey(
        "wireguard.WireguardServer",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="self_registrations",
    )

    class Meta:
        verbose_name = "Self Registration"
        verbose_name_plural = "Self Registrations"

    def __str__(self) -> str:
        return f"{self.email_domain}@{self.server}"
