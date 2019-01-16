#!/bin/sh
BASEDIR=$(readlink -f $(dirname $0)/..)
cp -rp ${BASEDIR} /usr/share
chmod 700 /usr/share/db_wlan_manager/network-manager/network-manager-dbwifi
chown root: /usr/share/db_wlan_manager/network-manager/network-manager-dbwifi

ln -sf /usr/share/db_wlan_manager/network-manager/network-manager-dbwifi /etc/NetworkManager/dispatcher.d/10-dbwifi
