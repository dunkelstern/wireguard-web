# Generated by Django 4.2 on 2023-04-21 22:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wireguard", "0010_public_key_datamigration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wireguardclient",
            name="public_key",
            field=models.CharField(blank=True, max_length=128, verbose_name="Public key"),
        ),
    ]
