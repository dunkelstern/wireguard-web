import re
import subprocess
from datetime import datetime
from hashlib import sha256


PUBKEY_CACHE: dict[str, str] = {}


def gen_key() -> str:
    try:
        result = subprocess.run(["wg", "genkey"], text=True, capture_output=True, check=True)
        key = result.stdout.strip()
        return key
    except subprocess.CalledProcessError:
        return None


def public_key_from_private(private_key: str) -> str:
    global PUBKEY_CACHE

    hash = sha256(private_key.encode("utf-8")).hexdigest()
    if hash in PUBKEY_CACHE.keys():
        return PUBKEY_CACHE[hash]
    try:
        result = subprocess.run(["wg", "pubkey"], input=private_key, text=True, capture_output=True, check=True)
        key = result.stdout.strip()
        PUBKEY_CACHE[hash] = key
        return key
    except subprocess.CalledProcessError:
        return None


def last_handshake(public_key: str) -> datetime:
    # TODO: Cache
    try:
        result = subprocess.run(["sudo", "wg", "show", "all", "latest-handshakes"], capture_output=True, check=True)
        for line in result.stdout.splitlines():
            interface, pubkey, timestamp = re.split(r"\s+", line.decode("UTF-8"), maxsplit=2)
            if pubkey == public_key:
                if int(timestamp) == 0:
                    return None
                return datetime.fromtimestamp(int(timestamp))
        return None
    except subprocess.CalledProcessError:
        return None


def endpoint(public_key: str) -> str:
    # TODO: Cache
    try:
        result = subprocess.run(["sudo", "wg", "show", "all", "endpoints"], capture_output=True, check=True)
        for line in result.stdout.splitlines():
            try:
                interface, pubkey, endpoint = re.split(r"\s+", line.decode("UTF-8"), maxsplit=1)
                if pubkey == public_key:
                    return endpoint
            except ValueError:
                pass
        return None
    except subprocess.CalledProcessError:
        return None


def format_network(ip: str, cidr: int = None) -> str:
    if "." in ip:
        # IPv4
        if cidr:
            return f"{ip}/{cidr}"
        else:
            return f"{ip}/32"
    elif ":" in ip:
        # IPv6
        if cidr:
            return f"{ip}/{cidr}"
        else:
            return f"{ip}/128"
    return None
