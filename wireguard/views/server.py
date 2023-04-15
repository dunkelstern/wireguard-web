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
        context["servers"] = WireguardServer.objects.allowed_servers_for_user(request.user)
        return self.render_to_response(context)


@method_decorator(login_required, name="dispatch")
class ServerDetailView(TemplateView):
    template_name = "wireguard/server_detail.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context["server"] = WireguardServer.objects.allowed_servers_for_user(request.user).get(pk=kwargs["id"])
            context["clients"] = WireguardClient.objects.filter(owner=request.user, server=context["server"])
        except WireguardServer.DoesNotExist:
            context["server"] = None
            context["clients"] = []
            messages.add_message(request, messages.ERROR, "No such server!")

        return self.render_to_response(context)
