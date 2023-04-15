# Generated by Django 4.2 on 2023-04-14 23:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wireguard", "0005_alter_wireguardclient_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServerAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateField(auto_now_add=True)),
                (
                    "server",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="wireguard.wireguardserver"),
                ),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Server Access",
                "verbose_name_plural": "Server Access",
                "unique_together": {("user", "server")},
            },
        ),
    ]