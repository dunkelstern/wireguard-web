from django.views.generic import TemplateView

from wireguard.models import WireguardClient, WireguardServer, WireguardServerSelfRegistration


class HomeView(TemplateView):
    template_name = "wireguard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domains = set()
        for reg in WireguardServerSelfRegistration.objects.all():
            domains.add(reg.email_domain)
        context["self_registrations"] = list(domains)
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated:
            context["servers"] = WireguardServer.objects.allowed_servers_for_user(request.user)
            context["clients"] = WireguardClient.objects.filter(owner=request.user)
        return self.render_to_response(context)
