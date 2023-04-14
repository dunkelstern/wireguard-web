#!/bin/bash

set -o allexport
source .env
set +o allexport

if [ $(id -u) -gt 0 ] ; then
    echo "Please run this script as root or via sudo"
    exit 1
fi

mkdir -p /etc/wireguard-web

# some path templating
path=$(pwd)
dnsmasq=${which dnsmasq}
wg=${which wg}
wgquick=${which wg-quick}

for file in wireguard-web-config.path wireguard-web-config.service wireguard-web-dnsmasq@.service wireguard-web-wg-quick@.service ; do
    tempfile=$(mktemp /tmp/service.XXXXXXXX)
    sed \
        -e "s@{path}@${path}@" \
        -e "s@{dnsmasq}@${dnsmasq}@" \
        -e "s@{wg}@${wg}@" \
        -e "s@{wgquick}@${wgquick}@" \
        -e "s@{config}@${WIREGUARD_STAGING_CONFIG_DIRECTORY}@" \
        systemd/$file >$tempfile
    install -o root -g root -m 0644 $tempfile /etc/systemd/system/$file
    rm $tempfile
done

systemctl daemon-reload
systemctl enable --now wireguard-web-config.path
