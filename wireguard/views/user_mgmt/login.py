from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


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
