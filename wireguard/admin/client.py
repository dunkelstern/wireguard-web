from django.contrib import admin
from django.http import HttpResponse

from wireguard.config_generators.wgquick import client_config
from wireguard.models import (
    WireguardClient,
    WireguardClientIP,
    WireguardClientLocalNetwork,
    WireguardClientNetworks,
    WireguardServer,
)


@admin.action(description="Generate wg-quick config")
def generate_wgquick(modeladmin, request, queryset):
    data = ""
    for item in queryset:
        data += f"<h2>{item.name}@{item.server.name}</h2><pre>"
        data += client_config(item)
        data += "</pre>\n"
    html = f"<!DOCTYPE html><html><head><title>Client config</title></head><body>{data}</body></html>"
    return HttpResponse(html)


class WireguardClientIPsInline(admin.TabularInline):
    model = WireguardClientIP
    fields = ("ip",)
    readonly_fields = ("ip",)
    extra = 0

    show_change_link = True

    def has_add_permission(self, request, obj):
        return False


class WireguardClientNetworksInline(admin.TabularInline):
    model = WireguardClientNetworks
    fields = ("ip",)
    readonly_fields = ("ip",)
    extra = 0

    show_change_link = True

    def has_add_permission(self, request, obj):
        return False


class WireguardClientLocalNetworksInline(admin.TabularInline):
    model = WireguardClientLocalNetwork
    fields = ("ip", "cidr_mask", "gateway", "public_ip")

    def has_change_permission(self, request, obj) -> bool:
        return False

    def has_add_permission(self, request, obj):
        return False


@admin.register(WireguardClient)
class WireguardClientAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "preshared_key", "owner", "server")}),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": ("use_dns", "keepalive", "route_all_traffic", "is_exitnode", "exit_interface"),
            },
        ),
        ("Information", {"fields": ("public_key", "endpoint", "port", "last_handshake")}),
    )
    readonly_fields = ("private_key", "public_key", "endpoint", "port", "last_handshake")
    list_display = ("name", "owner", "server", "route_all_traffic", "last_handshake")
    inlines = (WireguardClientIPsInline, WireguardClientNetworksInline, WireguardClientLocalNetworksInline)
    actions = (generate_wgquick,)

    def has_change_permission(self, request, obj=None) -> bool:
        has_permission = super().has_change_permission(request, obj)
        if has_permission and obj:
            return WireguardServer.objects.allowed_servers_for_user(request.user).filter(pk=obj.server.pk).count() > 0
        return has_permission

    def has_delete_permission(self, request, obj=None) -> bool:
        has_permission = super().has_delete_permission(request, obj)
        if has_permission and obj:
            return WireguardServer.objects.allowed_servers_for_user(request.user).filter(pk=obj.server.pk).count() > 0
        return has_permission
