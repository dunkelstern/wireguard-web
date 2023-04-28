from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


PERMISSIONS = {
    "Server Admins": [
        # view
        "view_wireguardserver",
        "view_wireguardclient",
        "view_wireguardserverselfregistration",
        "view_wireguardservernetworks",
        "view_wireguardclientnetworks",
        "view_wireguardclientip",
        "view_wireguardserverdnsoverrides",
        "view_wireguardclientlocalnetwork",
        "view_serveraccess",
        "view_user",
        # change
        "change_wireguardserver",
        "change_wireguardservernetworks",
        "change_wireguardserverdnsoverrides",
        # add
        "add_wireguardservernetworks",
        "add_wireguardserverdnsoverrides",
        # delete
        "delete_wireguardservernetworks",
        "delete_wireguardserverdnsoverrides",
    ],
    "Self Registration Admins": [
        # view
        "view_wireguardserver",
        "view_wireguardserverselfregistration",
        "view_wireguardservernetworks",
        "view_wireguardserverdnsoverrides",
        "view_user",
        "view_serveraccess",
        # change
        "change_wireguardserverselfregistration",
        # add
        "add_wireguardserverselfregistration",
        # delete
        "delete_wireguardserverselfregistration",
    ],
    "Client Admins": [
        # view
        "view_wireguardclient",
        "view_wireguardclientnetworks",
        "view_wireguardclientip",
        "view_wireguardclientlocalnetwork",
        "view_wireguardserverselfregistration",
        "view_wireguardservernetworks",
        "view_wireguardserverdnsoverrides",
        "view_serveraccess",
        "view_user",
        "view_wireguardserver",
        # change
        "change_wireguardclient",
        "change_wireguardclientnetworks",
        "change_wireguardclientip",
        "change_wireguardclientlocalnetwork",
        # add
        "add_wireguardclient",
        "add_wireguardclientnetworks",
        "add_wireguardclientip",
        "add_wireguardclientlocalnetwork",
        # delete
        "delete_wireguardclient",
        "delete_wireguardclientnetworks",
        "delete_wireguardclientip",
        "delete_wireguardclientlocalnetwork",
    ],
    "User Admins": [
        # view
        "view_user",
        "view_serveraccess",
        # change
        "change_user",
        "change_serveraccess",
        # add
        "add_user",
        "add_serveraccess",
        # delete
        "delete_user",
        "delete_serveraccess",
    ],
}


class Command(BaseCommand):
    help = "Create default groups"

    def handle(self, *args, **options):
        for groupname, permissions in PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=groupname)
            for perm in permissions:
                group.permissions.add(Permission.objects.get(codename=perm))
            group.save()
