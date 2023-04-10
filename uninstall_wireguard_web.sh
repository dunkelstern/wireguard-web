#!/bin/bash

if [ $(id -u) -gt 0 ] ; then
    echo "Please run this script as root or via sudo"
    exit 1
fi

systemctl disable --now wireguard-web-config.path
systemctl disable --now wireguard-web-wg-quick@\*.service
systemctl disable --now wireguard-web-dnsmasq@\*.service

for file in wireguard-web-config.path wireguard-web-config.service wireguard-web-dnsmasq@.service wireguard-web-wg-quick@.service ; do
    rm /etc/systemd/system/$file
done

systemctl daemon-reload

rm -rf /etc/wireguard-web
