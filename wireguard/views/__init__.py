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
from .p2p import PeeringView
from .server import ServerDetailView, ServerListView
from .user_mgmt import InviteView, LoginView, LogoutView, RegisterView, ResetPasswordView


__all__ = [
    "HomeView",
    "LoginView",
    "LogoutView",
    "ResetPasswordView",
    "RegisterView",
    "InviteView",
    "ServerListView",
    "ServerDetailView",
    "ClientListView",
    "ClientDetailView",
    "ClientDeleteView",
    "ClientNewView",
    "ClientSendConfigView",
    "ClientDownloadConfigView",
    "ClientQRConfigView",
    "PeeringView",
]
