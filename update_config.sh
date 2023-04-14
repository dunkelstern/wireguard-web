#!/bin/bash

set -o allexport
source .env
set +o allexport


if [ $(id -u) -gt 0 ] ; then
    echo "Please run this script as root or via sudo"
    exit 1
fi

echo "Using configuration from '$WIREGUARD_STAGING_CONFIG_DIRECTORY'"
mkdir -p /etc/wireguard-web

for interface in $(cat "${WIREGUARD_STAGING_CONFIG_DIRECTORY}"/interfaces.conf) ; do
    dnsmasq_config="${WIREGUARD_STAGING_CONFIG_DIRECTORY}/dnsmasq/dnsmasq-${interface}.conf"

    echo "Copying configuration for interface ${interface}..."

    echo " - wg-quick"
    install -o root -g root -m 0640 "${file}" "/etc/wireguard-web/${interface}.conf"

    if [ -f "${dnsmasq_config}" ] ; then
        echo " - dnsmasq"
        install -o root -g root -m 0640 "${dnsmasq_config}" "/etc/wireguard-web/dnsmasq-${interface}.conf"
    fi

    echo "Checking if services are enabled for ${interface}..."
    
    if [ "$(systemctl is-enabled wireguard-web-wg-quick@${interface})" = "disabled" ] ; then
        echo " - enabling wg-quick service now"
        systemctl enable --now wireguard-web-wg-quick@${interface}
    else
        echo " - reloading wg-quick"
        systemctl reload "wireguard-web-wg-quick@${interface}"
    fi

    if [ -f "${dnsmasq_config}" ] ; then
        if [ "$(systemctl is-enabled wireguard-web-dnsmasq@${interface})" = "disabled" ] ; then
            echo " - enabling dnsmasq service now"
            systemctl enable --now wireguard-web-dnsmasq@${interface}
        else
            echo " - restarting dnsmasq"
            systemctl restart "wireguard-web-dnsmasq@${interface}"
        fi
    fi
done
