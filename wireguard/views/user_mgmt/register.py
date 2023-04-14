from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.generic import TemplateView

from wireguard.models import WireguardServerSelfRegistration

from .login import LoginView
from .utils import send_reset_mail


User = get_user_model()


class RegisterView(TemplateView):
    template_name = "wireguard/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domains = set()
        for reg in WireguardServerSelfRegistration.objects.all():
            domains.add(reg.email_domain)
        context["self_registrations"] = list(domains)
        return context

    def post(self, request):
        username = request.POST["username"]
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = None

        try:
            _, domain = request.POST["username"].split("@", maxsplit=1)
        except ValueError:
            messages.add_message(request, messages.ERROR, "Please enter a valid e-mail address!")
            return redirect("register")

        if WireguardServerSelfRegistration.objects.filter(email_domain=domain.lower()).count() == 0:
            messages.add_message(request, messages.ERROR, "Sorry you cannot register with this domain!")
            return redirect("register")

        if user:
            messages.add_message(
                request, messages.ERROR, "User already existed, password reset instructions have been sent"
            )
            send_reset_mail(request, user, "wireguard/reset_password_mail.txt", "WireGuard Web Password Reset")
        else:
            messages.add_message(request, messages.SUCCESS, "Please look for a welcome mail")
            user = User.objects.create(email=request.POST["username"].lower(), name=request.POST["name"])
            send_reset_mail(request, user, "wireguard/welcome_mail.txt", "Welcome to WireGuard Web")

        return TemplateResponse(request, LoginView.template_name, {"username": request.POST["username"]})
