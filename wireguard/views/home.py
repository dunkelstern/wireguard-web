from django.views.generic import TemplateView

from wireguard.models import WireguardServerSelfRegistration


class HomeView(TemplateView):
    template_name = "wireguard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domains = set()
        for reg in WireguardServerSelfRegistration.objects.all():
            domains.add(reg.email_domain)
        context["self_registrations"] = list(domains)
        return context
