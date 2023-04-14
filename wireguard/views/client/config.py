from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from qrcode import QRCode

from wireguard.config_generators.wgquick import client_config
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
        config = client_config(client)

        # generate qr code
        qr = QRCode()
        qr.add_data(config)
        image = qr.make_image()
        buffer = BytesIO()
        image.save(buffer, "PNG")

        # compose mail
        template = loader.get_template("wireguard/config_mail.txt")
        link = settings.BASE_URL + reverse("client-detail", kwargs={"id": client.id})

        rendered = template.render({"server": settings.BASE_URL, "link": link, "user": request.user, "client": client})
        mail = EmailMessage(f"WireGuard configuration for {client.name}", rendered, None, [request.user.email])
        mail.attach(f"{client.name}.conf", config, "text/plain")
        mail.attach(f"{client.name}_qrcode.png", buffer.getvalue(), "image/png")
        mail.send(fail_silently=True)

        messages.add_message(request, messages.SUCCESS, "Configuration mail sent!")
        return redirect("client-list")

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context["client"] = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            context["client"] = None
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
        config = client_config(client)

        response = HttpResponse(config)
        response["Content-Type"] = "text/plain"
        response["Content-Disposition"] = f'attachment; filename="{client.name}.conf"'
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
        config = client_config(client)

        # generate qr code
        qr = QRCode()
        qr.add_data(config)
        image = qr.make_image()
        buffer = BytesIO()
        image.save(buffer, "PNG")

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "image/png"
        return response
