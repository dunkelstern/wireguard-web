import json
from datetime import datetime, timedelta
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_interface
from typing import Union

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from wireguard.models import WireguardClient, WireguardClientLocalNetwork


def same_ip(a: str, b: Union[IPv4Address, IPv6Address]) -> bool:
    a_ip = ip_address(a.strip("[]"))
    if isinstance(b, IPv4Address) and isinstance(a_ip, IPv4Address):
        if a == str(b):
            return True
    elif isinstance(b, IPv6Address) and isinstance(a_ip, IPv6Address):
        a_net = ip_interface(f"{a_ip}/64").network
        b_net = ip_interface(f"{b}/64").network
        if a_net == b_net:
            return True
    return False


@method_decorator(csrf_exempt, name="dispatch")
class PeeringView(View):
    def post(self, request, *args, **kwargs):
        # parse request json
        if request.content_type != "application/json":
            return JsonResponse({"error": "Only accepting application/json"}, status=400)

        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Could not decode JSON data"}, status=400)

        # validate request
        try:
            if isinstance(data, list):
                if len(data) < 1:
                    return JsonResponse({"error": "Empty request"}, status=400)
            else:
                data = [data]
            pubkey = data[0].get("pubkey")
        except (AttributeError, ValueError):
            return JsonResponse({"error": "Missing field, need 'pubkey', 'ip', 'netmask', 'gateway'"}, status=400)

        # check if we have a client with current handshake and endpoint address
        # that matches this request from address and pubkey
        remote_ip = ip_address(request.META.get("HTTP_X_FORWARDED_FOR", request.META["REMOTE_ADDR"]))
        try:
            client = WireguardClient.objects.get(public_key=pubkey)
            found = False
            for client_ip in client.ips.all():
                if same_ip(client_ip.ip, remote_ip):
                    found = True
            if not found:
                raise WireguardClient.DoesNotExist
            if client.last_handshake < datetime.now() - timedelta(minutes=10):
                return JsonResponse({"error": "Handshake too old"}, status=400)
            endpoint = client.endpoint
        except WireguardClient.DoesNotExist:
            return JsonResponse({"error": "Invalid client"}, status=401)

        # For DEBUGGING:
        # client = WireguardClient.objects.get(pk=int(pubkey))
        # endpoint = "10.10.10.0"

        endpoint = ip_address(endpoint.strip("[]"))

        client.local_networks.all().delete()
        for item in data:
            ip = ip_address(item.get("ip"))
            gateway = str(ip_address(item.get("gateway")))
            netmask = item.get("netmask")

            if endpoint == ip:
                continue

            # update local networks of the client
            WireguardClientLocalNetwork.objects.create(
                public_ip=endpoint, gateway=gateway, cidr_mask=netmask, client=client, ip=str(ip)
            )

        # check if we have a p2p enabled client here, send all known vpn peers
        # to those but keep out the endpoint addresses
        if client.allow_direct_peering:
            peers = []

            for item in data:
                ip = ip_address(item.get("ip"))
                gateway = str(ip_address(item.get("gateway")))
                netmask = item.get("netmask")

                clients = (
                    WireguardClient.objects.filter(
                        local_networks__gateway=gateway, local_networks__cidr_mask=netmask, server=client.server
                    )
                    .exclude(pk=client.pk)
                    .exclude(route_all_traffic=True)
                )
                for local_client in clients:
                    found = False
                    for client_ip in local_client.local_networks.all():
                        if same_ip(client_ip.public_ip, endpoint):
                            found = True
                    if found:
                        p = {
                            "pubkey": local_client.public_key,
                            "ip": list(local_client.ips.all().values_list("ip", flat=True)),
                        }
                        if p not in peers:
                            peers.append(p)

            return JsonResponse({"peers": peers})
        else:
            # not p2p target enabled: send all peers in the local network of the
            # client with endpoint addresses
            peers = []

            for item in data:
                ip = ip_address(item.get("ip"))
                gateway = str(ip_address(item.get("gateway")))
                netmask = item.get("netmask")

                clients = (
                    WireguardClient.objects.filter(
                        local_networks__gateway=gateway, local_networks__cidr_mask=netmask, server=client.server
                    )
                    .exclude(pk=client.pk)
                    .exclude(route_all_traffic=True)
                )
                for peer in clients:
                    found = False
                    for client_ip in client.local_networks.all():
                        if same_ip(client_ip.public_ip, endpoint):
                            found = True
                    if not found:
                        continue

                    p2p_endpoint = None
                    for net in peer.local_networks.all():
                        if net.is_ipv4:
                            p2p_endpoint = net.ip
                    if not p2p_endpoint:
                        p2p_endpoint = peer.local_networks.first().ip

                    p = {
                        "pubkey": peer.public_key,
                        "endpoint": p2p_endpoint,
                        "port": peer.port,
                        "ip": list(peer.ips.all().values_list("ip", flat=True)),
                    }

                    if p not in peers:
                        peers.append(p)
            return JsonResponse({"peers": peers})
