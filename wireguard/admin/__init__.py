from .client import WireguardClientAdmin
from .server import WireguardServerAdmin
from .user import UserAdmin


__all__ = [
    "UserAdmin",
    "WireguardServerAdmin",
    "WireguardClientAdmin"
]
