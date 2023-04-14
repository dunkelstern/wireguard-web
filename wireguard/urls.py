"""wireguard_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from wireguard.views import (
    ClientDeleteView,
    ClientDetailView,
    ClientDownloadConfigView,
    ClientListView,
    ClientNewView,
    ClientQRConfigView,
    ClientSendConfigView,
    HomeView,
    LoginView,
    LogoutView,
    RegisterView,
    ResetPasswordView,
    ServerDetailView,
    ServerListView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password"),
    path("register", RegisterView.as_view(), name="register"),
    path("server-list", ServerListView.as_view(), name="server-list"),
    path("server/<int:id>", ServerDetailView.as_view(), name="server-detail"),
    path("client-list", ClientListView.as_view(), name="client-list"),
    path("client/<int:id>", ClientDetailView.as_view(), name="client-detail"),
    path("client-delete/<int:id>", ClientDeleteView.as_view(), name="client-delete"),
    path("client-new", ClientNewView.as_view(), name="client-new"),
    path("client-send/<int:id>/<str:typ>", ClientSendConfigView.as_view(), name="client-send-config"),
    path("client-config/<int:id>/<str:typ>", ClientDownloadConfigView.as_view(), name="client-download-config"),
    path("client-qr/<int:id>", ClientQRConfigView.as_view(), name="client-qr-config"),
]
