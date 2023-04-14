# Generated by Django 4.2 on 2023-04-14 14:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wireguard", "0002_wireguardserver_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordReset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_count", models.IntegerField(verbose_name="Number of password resets in a row")),
                ("last_request_date", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="password_reset",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Password reset",
                "verbose_name_plural": "Password resets",
            },
        ),
    ]
