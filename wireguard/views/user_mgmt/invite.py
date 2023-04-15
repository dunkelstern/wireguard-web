from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import Http404
from django.views.generic import TemplateView

from wireguard.models import ServerAccess, WireguardServer

from .utils import send_reset_mail


User = get_user_model()


class InviteView(TemplateView):
    template_name = "wireguard/invite.html"

    def post(self, request, **kwargs):
        username = request.POST["username"]
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = None

        if user:
            for sv_id in request.POST.getlist("servers"):
                server = WireguardServer.objects.get(pk=sv_id)
                if not ServerAccess.objects.filter(user=user, server=server).exists():
                    ServerAccess.objects.create(user=user, server=server)
            messages.add_message(
                request,
                messages.ERROR,
                "User already existed, password reset instructions have been sent and server access has been granted",
            )
            send_reset_mail(request, user, "wireguard/reset_password_mail.txt", "WireGuard Web Password Reset")
        else:
            messages.add_message(request, messages.SUCCESS, "User has been invited successfully!")
            user = User.objects.create(email=request.POST["username"].lower(), name=request.POST["name"])
            for sv_id in request.POST.getlist("servers"):
                server = WireguardServer.objects.get(pk=sv_id)
                ServerAccess.objects.create(user=user, server=server)
            send_reset_mail(request, user, "wireguard/invite_mail.txt", "Invitation to WireGuard Web")

        return self.get(request, **kwargs)

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_staff:
            context["servers"] = WireguardServer.objects.allowed_servers_for_user(request.user)
            return self.render_to_response(context)
        else:
            return Http404
