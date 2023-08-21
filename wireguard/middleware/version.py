from subprocess import run

import pkg_resources


KERNEL_VERSION = run(["uname", "-r"], capture_output=True, text=True).stdout.strip()
KERNEL = run(["uname", "-s"], capture_output=True, text=True).stdout.strip()
VERSION = pkg_resources.require("wireguard-web")[0].version


class VersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "installed_version", VERSION)
        setattr(request, "kernel_version", KERNEL_VERSION)
        setattr(request, "kernel", KERNEL)
        response = self.get_response(request)
        return response
