# Generated by Django 4.2 on 2023-04-10 18:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import wireguard.models.user


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email address")),
                ("name", models.CharField(blank=True, max_length=128, verbose_name="name")),
                ("date_joined", models.DateTimeField(auto_now_add=True, verbose_name="date joined")),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[
                ("objects", wireguard.models.user.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="WireguardClient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True, verbose_name="Client name")),
                ("private_key", models.CharField(blank=True, max_length=128, verbose_name="Private key")),
                (
                    "preshared_key",
                    models.CharField(blank=True, max_length=128, null=True, verbose_name="Pre-Shared Key, optional"),
                ),
                ("keepalive", models.IntegerField(default=0, verbose_name="Persistent keepalive timeout")),
                ("use_dns", models.BooleanField(default=False, verbose_name="Use the DNS of the server")),
                (
                    "route_all_traffic",
                    models.BooleanField(default=False, verbose_name="Route all traffic through this Connection"),
                ),
                (
                    "is_exitnode",
                    models.BooleanField(
                        default=False, verbose_name="This client is a NAT gateway/exit node to a bridged network"
                    ),
                ),
                (
                    "exit_interface",
                    models.CharField(
                        blank=True,
                        default=None,
                        max_length=16,
                        null=True,
                        verbose_name="Network interface to which to route external traffic",
                    ),
                ),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="WireguardServer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True, verbose_name="Server name")),
                ("interface_name", models.CharField(max_length=16, unique=True, verbose_name="Network interface name")),
                ("hostname", models.CharField(max_length=128, verbose_name="Server host-name or IP")),
                ("private_key", models.CharField(blank=True, max_length=128, verbose_name="Private key")),
                ("port", models.IntegerField(default=44000, verbose_name="Listening port")),
                ("fw_mark", models.IntegerField(default=0, verbose_name="FWMark for outgoing packets")),
                ("keepalive", models.IntegerField(default=0, verbose_name="Persistent keepalive timeout")),
                ("has_dns", models.BooleanField(default=False, verbose_name="This server has a DNS resolver")),
                (
                    "dns_domain",
                    models.CharField(
                        default="vpn.local",
                        max_length=128,
                        verbose_name="Domain name for all clients when DNS is enabled",
                    ),
                ),
                (
                    "is_exitnode",
                    models.BooleanField(default=False, verbose_name="This server is a NAT gateway/exit node"),
                ),
                (
                    "exit_interface",
                    models.CharField(
                        blank=True,
                        default=None,
                        max_length=16,
                        null=True,
                        verbose_name="Network interface to which to route external traffic",
                    ),
                ),
                (
                    "clients_may_communicate",
                    models.BooleanField(default=True, verbose_name="Clients may communicate with each other"),
                ),
                (
                    "may_route_all_traffic",
                    models.BooleanField(
                        default=False, verbose_name="Clients may access the Internet through this server"
                    ),
                ),
                (
                    "allow_client_bridges",
                    models.BooleanField(default=False, verbose_name="Clients may bridge to their Network"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WireguardServerSelfRegistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "email_domain",
                    models.CharField(
                        max_length=128, verbose_name="Users with this e-mail domain may self-register on this Server"
                    ),
                ),
                (
                    "server",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="self_registrations",
                        to="wireguard.wireguardserver",
                    ),
                ),
            ],
            options={
                "verbose_name": "Self Registration",
                "verbose_name_plural": "Self Registrations",
            },
        ),
        migrations.CreateModel(
            name="WireguardServerNetworks",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip", models.GenericIPAddressField(unpack_ipv4=True, verbose_name="IP Address of server in Network")),
                (
                    "cidr_mask",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        null=True,
                        verbose_name="If set, automatically update the client's allowed IPs to route to this net",
                    ),
                ),
                (
                    "is_client_network",
                    models.BooleanField(default=False, verbose_name="Clients will get IPs from this network"),
                ),
                (
                    "server",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="networks",
                        to="wireguard.wireguardserver",
                    ),
                ),
            ],
            options={
                "verbose_name": "Network",
                "verbose_name_plural": "Networks",
            },
        ),
        migrations.CreateModel(
            name="WireguardClientNetworks",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip", models.GenericIPAddressField(unpack_ipv4=True, verbose_name="IP Network")),
                ("cidr_mask", models.IntegerField(verbose_name="Netmask in CIDR form for this network")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="networks",
                        to="wireguard.wireguardclient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Network",
                "verbose_name_plural": "Networks",
            },
        ),
        migrations.CreateModel(
            name="WireguardClientIP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip", models.GenericIPAddressField(unpack_ipv4=True, verbose_name="IP Address of client in Network")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="ips", to="wireguard.wireguardclient"
                    ),
                ),
            ],
            options={
                "verbose_name": "IP Address",
                "verbose_name_plural": "IP Addresses",
            },
        ),
        migrations.AddField(
            model_name="wireguardclient",
            name="server",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="clients", to="wireguard.wireguardserver"
            ),
        ),
        migrations.CreateModel(
            name="WireguardServerDNSOverrides",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(max_length=255, verbose_name="Domain name")),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("A", "IPv4 address record (A)"),
                            ("AAAA", "IPv6 address record (AAAA)"),
                            ("CNAME", "Domain Alias (CNAME)"),
                            ("MX", "Mail Server (MX)"),
                            ("TXT", "Text Record (TXT)"),
                            ("SRV", "Service Record (SRV)"),
                        ],
                        default="A",
                        max_length=32,
                        verbose_name="DNS entry type",
                    ),
                ),
                ("value", models.CharField(blank=True, default="", max_length=1024, verbose_name="Record value")),
                (
                    "server",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="dns", to="wireguard.wireguardserver"
                    ),
                ),
            ],
            options={
                "verbose_name": "DNS Override",
                "verbose_name_plural": "DNS Overrides",
                "unique_together": {("domain", "type", "server")},
            },
        ),
    ]
