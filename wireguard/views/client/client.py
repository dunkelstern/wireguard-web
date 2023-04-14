from ipaddress import ip_network

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from wireguard.models import WireguardClient, WireguardClientNetworks, WireguardServer


@method_decorator(login_required, name="dispatch")
class ClientListView(TemplateView):
    template_name = "wireguard/device_list.html"

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        context["clients"] = WireguardClient.objects.filter(owner=request.user)
        return self.render_to_response(context)


@method_decorator(login_required, name="dispatch")
class ClientDetailView(TemplateView):
    template_name = "wireguard/device_detail.html"

    def post(self, request, **kwargs):
        error = False
        to_save = []

        try:
            client = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such device!")
            return redirect("client-list")

        client.name = request.POST["name"]
        client.keepalive = int(request.POST["keepalive"])
        client.use_dns = request.POST.get("use_dns", "0") == "1"
        client.route_all_traffic = request.POST.get("route_all_traffic", "0") == "1"
        client.is_exitnode = request.POST.get("is_exitnode", "0") == "1"
        client.exit_interface = request.POST.get("exit_interface", "")
        if client.is_exitnode and not client.exit_interface:
            messages.add_message(
                request,
                messages.ERROR,
                "When selecting to bridge to an internal network you need to set the exit interface!",
            )
            error = True
        to_save.append(client)

        # edited old bridges
        for bridge in client.networks.all():
            if request.POST[f"bridge_{bridge.id}"]:
                # update the bridge
                try:
                    n = ip_network(request.POST[f"bridge_{bridge.id}"])
                    net = WireguardClientNetworks.objects.get(client=client, id=bridge.id)
                    net.ip = str(n.network_address)
                    net.cidr_mask = n.prefixlen
                    to_save.append(net)
                except ValueError:
                    messages.add_message(request, messages.ERROR, "Adding of new Network failed, wrong format!")
                    error = True
            else:
                # remove the bridge
                try:
                    WireguardClientNetworks.objects.get(client=client, id=bridge.id).delete()
                except WireguardClientNetworks.DoesNotExist:
                    pass

        # new bridges
        for bridge in ("bridge_new_1", "bridge_new_2"):
            if request.POST.get(bridge):
                try:
                    net = ip_network(request.POST[bridge])
                    to_save.append(
                        WireguardClientNetworks(client=client, ip=str(net.network_address), cidr_mask=net.prefixlen)
                    )
                except ValueError:
                    messages.add_message(request, messages.ERROR, "Adding of new Network failed, wrong format!")
                    error = True

        if error:
            context = self.get_context_data(**kwargs)
            context["client"] = client
            context["bridge_new_1"] = request.POST["bridge_new_1"]
            context["brigde_new_2"] = request.POST["bridge_new_2"]
            return self.render_to_response(context)

        for item in to_save:
            item.save()
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
class ClientDeleteView(TemplateView):
    template_name = "wireguard/device_delete.html"

    def post(self, request, **kwargs):
        try:
            client = WireguardClient.objects.get(owner=request.user, pk=kwargs["id"])
        except WireguardClient.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such device!")
            return redirect("client-list")

        client.delete()
        messages.add_message(request, messages.SUCCESS, "Device deleted!")
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
class ClientNewView(TemplateView):
    template_name = "wireguard/device_detail.html"

    def post(self, request, **kwargs):
        _, domain = request.user.email.split("@")
        try:
            server = WireguardServer.objects.get(self_registrations__email_domain=domain, pk=request.POST["server"])
            client = WireguardClient.objects.create(
                name=request.POST["name"], keepalive=int(request.POST["keepalive"]), server=server, owner=request.user
            )
        except WireguardServer.DoesNotExist:
            messages.add_message(request, messages.ERROR, "No such server!")

        return redirect("client-detail", id=client.id)

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        _, domain = request.user.email.split("@")
        context["client"] = WireguardClient()
        context["servers"] = WireguardServer.objects.filter(self_registrations__email_domain=domain)
        return self.render_to_response(context)
