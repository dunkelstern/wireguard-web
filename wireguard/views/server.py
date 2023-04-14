from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from wireguard.models import WireguardClient, WireguardServer


@method_decorator(login_required, name="dispatch")
class ServerListView(TemplateView):
    template_name = "wireguard/server_list.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        _, domain = request.user.email.split("@")
        context["servers"] = WireguardServer.objects.filter(self_registrations__email_domain=domain).order_by("name")
        return self.render_to_response(context)


@method_decorator(login_required, name="dispatch")
class ServerDetailView(TemplateView):
    template_name = "wireguard/server_detail.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        _, domain = request.user.email.split("@")
        try:
            context["server"] = WireguardServer.objects.get(self_registrations__email_domain=domain, pk=kwargs["id"])
            context["clients"] = WireguardClient.objects.filter(owner=request.user, server=context["server"]).order_by(
                "server", "name"
            )
        except WireguardServer.DoesNotExist:
            context["server"] = None
            context["clients"] = []
            messages.add_message(request, messages.ERROR, "No such server!")

        return self.render_to_response(context)
