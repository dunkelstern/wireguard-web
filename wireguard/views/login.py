from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template import loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views.generic import TemplateView

from wireguard.models import PasswordReset, WireguardServerSelfRegistration


User = get_user_model()


def send_reset_mail(request, user: User, template: str, subject: str):
    generator = PasswordResetTokenGenerator()
    template = loader.get_template(template)
    link = (
        settings.BASE_URL
        + reverse("reset-password")
        + "?"
        + urlencode({"token": generator.make_token(user), "email": user.email})
    )

    rendered = template.render({"server": settings.BASE_URL, "link": link, "name": user.name})
    send_mail(subject, rendered, None, [user.email], fail_silently=True)


class LoginView(TemplateView):
    template_name = "wireguard/login.html"

    def post(self, request):
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            messages.add_message(request, messages.ERROR, "Username or password not correct")
            return TemplateResponse(request, LoginView.template_name, {"username": request.POST["username"]})
        return redirect("home")


@method_decorator(login_required, name="dispatch")
class LogoutView(TemplateView):
    template_name = "wireguard/logout.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class ResetPasswordView(TemplateView):
    template_name = "wireguard/reset_password.html"

    def validate_token(self, request, token: str, email: str) -> User:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.add_message(request, messages.ERROR, "This reset-link is not valid anymore")
            return None

        generator = PasswordResetTokenGenerator()
        if not generator.check_token(user, token):
            messages.add_message(request, messages.ERROR, "This reset-link is not valid anymore")
            return None

        return user

    def get(self, request, **kwargs):
        token = request.GET.get("token", None)

        if token:
            user = self.validate_token(request, token, request.GET["email"])
            if not user:
                return TemplateResponse(request, ResetPasswordView.template_name, {"username": request.GET["email"]})

        context = self.get_context_data(**kwargs)
        if token:
            context.update({"token": token, "user": user})
        return self.render_to_response(context)

    def post(self, request, **kwargs):
        token = request.POST.get("token", None)

        if token:
            user = self.validate_token(request, token, request.POST["email"])
            if not user:
                return TemplateResponse(request, ResetPasswordView.template_name, {"username": request.POST["email"]})

            # password does not match?
            if request.POST["password"] != request.POST["password2"]:
                messages.add_message(request, messages.ERROR, "Passwords do not match")
                context = self.get_context_data(**kwargs)
                context.update({"token": token, "user": user})
                return self.render_to_response(context)

            # password too short?
            if len(request.POST["password"]) < 11:
                messages.add_message(request, messages.ERROR, "Minimum length of password is 11 characters")
                context = self.get_context_data(**kwargs)
                context.update({"token": token, "user": user})
                return self.render_to_response(context)

            user.set_password(request.POST["password"])
            user.save()

            messages.add_message(request, messages.SUCCESS, "Password successfully changed!")
            return TemplateResponse(request, LoginView.template_name, {"username": request.POST["email"]})

        # no token, send reset
        username = request.POST["username"]
        try:
            user = User.objects.get(email=username)
            try:
                user.password_reset

                # rate limit 1 per 30 seconds
                if user.password_reset.last_request_date > timezone.now() - timedelta(seconds=30):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Last password reset instruction was sent "
                        f"{int((timezone.now() - user.password_reset.last_request_date).total_seconds())} seconds ago, "
                        "please wait at least 30 seconds for next try.",
                    )
                    return TemplateResponse(request, ResetPasswordView.template_name, {"username": username})
                # rate limit 10 in 24 hours
                if (
                    user.password_reset.request_count >= 10
                    and user.password_reset.last_request_date > timezone.now() - timedelta(hours=24)
                ):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Password reset requested more than 10 times in the past 24 hours, "
                        " please wait at least one day for next try.",
                    )
                    return TemplateResponse(request, LoginView.template_name, {"username": username})
                # reset the rate limit after 24 hours
                if user.password_reset.last_request_date < timezone.now() - timedelta(hours=24):
                    user.password_reset.request_count = 0
                user.password_reset.request_count += 1
                user.password_reset.save()
            except User.password_reset.RelatedObjectDoesNotExist:
                PasswordReset.objects.create(user=user, request_count=1)
            send_reset_mail(request, user, "wireguard/reset_password_mail.txt", "WireGuard Web Password Reset")
        except User.DoesNotExist:
            pass

        messages.add_message(request, messages.SUCCESS, "Password reset instructions have been sent")
        return TemplateResponse(request, LoginView.template_name, {"username": request.POST["username"]})


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
