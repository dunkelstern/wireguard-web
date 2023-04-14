import os

from django.conf import settings
from qrcode import QRCode

from wireguard.config_generators.dnsmasq import dns_config
from wireguard.config_generators.wgquick import client_config, server_config
from wireguard.models import WireguardServer
from wireguard.signals import update_config


def create_dirs():
    if not os.path.exists(settings.CONFIG_DIRECTORY):
        os.makedirs(settings.CONFIG_DIRECTORY)
        os.makedirs(os.path.join(settings.CONFIG_DIRECTORY, "wg-quick"))
        os.makedirs(os.path.join(settings.CONFIG_DIRECTORY, "dnsmasq"))
        os.makedirs(os.path.join(settings.CONFIG_DIRECTORY, "clients"))


def save_enabled_interfaces():
    with open(os.path.join(settings.CONFIG_DIRECTORY, "interfaces.conf"), "w") as fp:
        for server in WireguardServer.objects.filter(enabled=True):
            fp.write(server.interface_name + "\n")


def update_server_config(sender, server, **kwargs):
    create_dirs()

    config_file = os.path.join(settings.CONFIG_DIRECTORY, "wg-quick", f"{server.interface_name}.conf")
    with open(config_file, "w") as fp:
        fp.write(server_config(server))

    config_file = os.path.join(settings.CONFIG_DIRECTORY, "dnsmasq", f"dnsmasq-{server.interface_name}.conf")
    with open(config_file, "w") as fp:
        fp.write(dns_config(server))

    for client in server.clients.all():
        config_file = os.path.join(settings.CONFIG_DIRECTORY, "clients", f"{client.name}@{server.name}.conf")
        with open(config_file, "w") as fp:
            conf = client_config(client)
            fp.write(conf)

        image_file = os.path.join(settings.CONFIG_DIRECTORY, "clients", f"{client.name}@{server.name}.png")
        qr = QRCode()
        qr.add_data(conf)
        image = qr.make_image()
        image.save(image_file, "PNG")

    save_enabled_interfaces()


update_config.connect(update_server_config, dispatch_uid="server_update")
