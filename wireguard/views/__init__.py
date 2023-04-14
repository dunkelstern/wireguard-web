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
from .server import ServerDetailView, ServerListView
from .user_mgmt import LoginView, LogoutView, RegisterView, ResetPasswordView


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
