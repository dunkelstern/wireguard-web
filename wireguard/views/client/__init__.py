from .client import ClientDeleteView, ClientDetailView, ClientListView, ClientNewView
from .config import ClientDownloadConfigView, ClientQRConfigView, ClientSendConfigView


__all__ = [
    "ClientListView",
    "ClientDetailView",
    "ClientDeleteView",
    "ClientNewView",
    "ClientSendConfigView",
    "ClientDownloadConfigView",
    "ClientQRConfigView",
]
