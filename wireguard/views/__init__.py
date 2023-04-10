from .client import (
    ClientDeleteView,
    ClientDetailView,
    ClientDownloadConfigView,
    ClientListView,
    ClientNewView,
    ClientQRConfigView,
    ClientSendConfigView,
)
from .home import HomeView
from .login import LoginView, LogoutView, RegisterView, ResetPasswordView
from .server import ServerDetailView, ServerListView


__all__ = [
    "HomeView",
    "LoginView",
    "LogoutView",
    "ResetPasswordView",
    "RegisterView",
    "ServerListView",
    "ServerDetailView",
    "ClientListView",
    "ClientDetailView",
    "ClientDeleteView",
    "ClientNewView",
    "ClientSendConfigView",
    "ClientDownloadConfigView",
    "ClientQRConfigView",
]
