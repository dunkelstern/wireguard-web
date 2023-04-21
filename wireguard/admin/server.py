from django.contrib import admin
from django.http import HttpResponse

from wireguard.config_generators.dnsmasq import dns_config
from wireguard.config_generators.wgquick import server_config
from wireguard.models import (
    WireguardClient,
    WireguardServer,
    WireguardServerDNSOverrides,
    WireguardServerNetworks,
    WireguardServerSelfRegistration,
)


@admin.action(description="Generate wg-quick config")
def generate_wgquick(modeladmin, request, queryset):
    data = ""
    for item in queryset:
        data += f"<h2>{item.name} ({item.interface_name})</h2><pre>"
        data += server_config(item)
        data += "</pre>\n"
    html = f"<!DOCTYPE html><html><head><title>Server config</title></head><body>{data}</body></html>"
    return HttpResponse(html)


@admin.action(description="Generate dnsmasq config")
def generate_dnsconfig(modeladmin, request, queryset):
    data = ""
    for item in queryset:
        if item.has_dns:
            data += f"<h2>{item.name} ({item.interface_name})</h2><pre>"
            data += dns_config(item)
            data += "</pre>\n"
    html = f"<!DOCTYPE html><html><head><title>DNS config</title></head><body>{data}</body></html>"
    return HttpResponse(html)


class WireguardServerNetworksInline(admin.TabularInline):
    model = WireguardServerNetworks
    fields = ("ip", "cidr_mask", "is_client_network")


class WireguardServerSelfRegistrationInline(admin.TabularInline):
    model = WireguardServerSelfRegistration
    fields = ("email_domain",)


class ClientInline(admin.TabularInline):
    model = WireguardClient
    fields = ("name", "last_handshake", "endpoint", "port")
    readonly_fields = ("name", "last_handshake", "endpoint", "port")
    extra = 0

    show_change_link = True

    def has_add_permission(self, request, obj):
        return False


class DNSOverrideInline(admin.TabularInline):
    model = WireguardServerDNSOverrides
    fields = ("type", "domain", "value")


@admin.register(WireguardServer)
class WireguardServerAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "interface_name",
                    "hostname",
                    "port",
                    "enabled",
                )
            },
        ),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": (
                    "has_dns",
                    "dns_domain",
                    "is_exitnode",
                    "exit_interface",
                    "may_route_all_traffic",
                    "clients_may_communicate",
                    "allow_client_bridges",
                    "allow_direct_peering",
                    "keepalive",
                    "fw_mark",
                ),
            },
        ),
        ("Information", {"fields": ("public_key",)}),
    )
    readonly_fields = (
        "private_key",
        "public_key",
    )
    list_display = ("interface_name", "name", "port", "is_exitnode", "has_dns")
    inlines = (WireguardServerNetworksInline, DNSOverrideInline, WireguardServerSelfRegistrationInline, ClientInline)
    actions = [generate_wgquick, generate_dnsconfig]

    def has_change_permission(self, request, obj=None) -> bool:
        has_permission = super().has_change_permission(request, obj)
        if has_permission and obj:
            return WireguardServer.objects.allowed_servers_for_user(request.user).filter(pk=obj.pk).count() > 0
        return has_permission

    def has_delete_permission(self, request, obj=None) -> bool:
        has_permission = super().has_delete_permission(request, obj)
        if has_permission and obj:
            return WireguardServer.objects.allowed_servers_for_user(request.user).filter(pk=obj.pk).count() > 0
        return has_permission
