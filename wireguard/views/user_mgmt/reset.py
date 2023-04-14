from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.generic import TemplateView

from wireguard.models import PasswordReset

from .login import LoginView
from .utils import send_reset_mail


User = get_user_model()


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
