from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from qrcode import QRCode

from wireguard.config_generators.netctl import netctl
from wireguard.config_generators.networkmanager import client_config as networkmanager
from wireguard.config_generators.systemd import netdev, network
from wireguard.config_generators.wgquick import client_config as wg_quick
from wireguard.models import WireguardClient


@method_decorator(login_required, name="dispatch")
class ClientSendConfigView(TemplateView):
    template_name = "wireguard/send_config.html"

    def post(self, request, **kwargs):
        try:
            client = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such device!")
            return redirect("client-list")

        # generate config
        if kwargs["typ"] == "wg-quick":
            config = wg_quick(client)
            filename = f"{client.server.interface_name}.conf"

            # generate qr code
            qr = QRCode()
            qr.add_data(config)
            image = qr.make_image()
            buffer = BytesIO()
            image.save(buffer, "PNG")
        elif kwargs["typ"] == "nmconnection":
            config = networkmanager(client)
            filename = f"{client.server.name}.nmconnection"
        elif kwargs["typ"] == "systemd.netdev":
            config = netdev(client)
            filename = f"{client.server.interface_name}.netdev"
        elif kwargs["typ"] == "systemd.network":
            config = network(client)
            filename = f"{client.server.interface_name}.network"
        elif kwargs["typ"] == "netctl":
            config = netctl(client)
            filename = f"{client.server.interface_name}"
        else:
            return HttpResponseBadRequest()

        # compose mail
        template = loader.get_template("wireguard/config_mail.txt")
        link = settings.BASE_URL + reverse("client-detail", kwargs={"id": client.id})

        rendered = template.render({"server": settings.BASE_URL, "link": link, "user": request.user, "client": client})
        mail = EmailMessage(f"WireGuard configuration for {client.name}", rendered, None, [request.user.email])
        mail.attach(filename, config, "text/plain")

        if kwargs["typ"] == "wg-quick":
            mail.attach(f"{client.name}_qrcode.png", buffer.getvalue(), "image/png")

        mail.send(fail_silently=True)

        messages.add_message(request, messages.SUCCESS, "Configuration mail sent!")
        return redirect("client-list")

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context["client"] = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
            context["config_type"] = kwargs["typ"]
        except WireguardClient.DoesNotExist:
            context["client"] = None
            context["config_type"] = kwargs["typ"]
            messages.add_message(request, messages.ERROR, "No such device!")
        return self.render_to_response(context)


@method_decorator(login_required, name="dispatch")
class ClientDownloadConfigView(View):
    def get(self, request, **kwargs):
        try:
            client = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such device!")
            return redirect("client-list")

        # generate config
        if kwargs["typ"] == "wg-quick":
            config = wg_quick(client)
            filename = f"{client.server.interface_name}.conf"
        elif kwargs["typ"] == "nmconnection":
            config = networkmanager(client)
            filename = f"{client.server.name}.nmconnection"
        elif kwargs["typ"] == "systemd.netdev":
            config = netdev(client)
            filename = f"{client.server.interface_name}.netdev"
        elif kwargs["typ"] == "systemd.network":
            config = network(client)
            filename = f"{client.server.interface_name}.network"
        elif kwargs["typ"] == "netctl":
            config = netctl(client)
            filename = f"{client.server.interface_name}"
        else:
            return HttpResponseBadRequest()

        response = HttpResponse(config)
        response["Content-Type"] = "text/plain"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@method_decorator(login_required, name="dispatch")
class ClientQRConfigView(View):
    def get(self, request, **kwargs):
        try:
            client = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such device!")
            return redirect("client-list")

        # generate config
        config = wg_quick(client)

        # generate qr code
        qr = QRCode()
        qr.add_data(config)
        image = qr.make_image()
        buffer = BytesIO()
        image.save(buffer, "PNG")

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "image/png"
        return response
