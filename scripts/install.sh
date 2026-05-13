#!/usr/bin/env bash
set -euo pipefail

# SpotMan Installation Script
# Must be run as root

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

SPOTMAN_DIR=$(dirname $(readlink -f "$0"))/..
cd $SPOTMAN_DIR

echo "[*] Setting up Nginx for SpotMan Sinkhole..."
cp backend/config/nginx.conf.template /etc/nginx/sites-available/spotman
ln -sf /etc/nginx/sites-available/spotman /etc/nginx/sites-enabled/spotman
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo "[*] Setting up Systemd Service..."
cp backend/systemd/spotman.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable spotman.service

echo "[*] Setting up Sudoers rules..."
# Allow anyone in the sudo group to run these commands passwordless
cat << EOF > /etc/sudoers.d/spotman
# SpotMan sudo rules for backend process
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl start hostapd
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl start dnsmasq
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl stop hostapd
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl stop dnsmasq
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl reload dnsmasq
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl is-active hostapd
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl is-active dnsmasq
%sudo ALL=(ALL) NOPASSWD: /sbin/iw dev *
%sudo ALL=(ALL) NOPASSWD: /sbin/iw *
%sudo ALL=(ALL) NOPASSWD: /sbin/tc *
%sudo ALL=(ALL) NOPASSWD: /sbin/iptables *
%sudo ALL=(ALL) NOPASSWD: /sbin/sysctl -w net.ipv4.ip_forward=1
%sudo ALL=(ALL) NOPASSWD: /bin/ip addr *
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl restart hostapd
%sudo ALL=(ALL) NOPASSWD: /bin/systemctl restart dnsmasq
%sudo ALL=(ALL) NOPASSWD: /bin/cp /tmp/spotman_hostapd.conf /etc/hostapd/hostapd.conf
%sudo ALL=(ALL) NOPASSWD: /bin/cp /tmp/spotman_dnsmasq.conf /etc/dnsmasq.d/spotman.conf
EOF
chmod 0440 /etc/sudoers.d/spotman

echo "[*] Ensuring dependencies..."
apt-get update
apt-get install -y hostapd dnsmasq nginx iw iproute2 iptables sqlite3 python3-venv

echo "[*] Configuring default hostapd path..."
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|g' /etc/default/hostapd || true

echo "[*] Unmasking hostapd service..."
systemctl unmask hostapd
systemctl enable hostapd

echo "[*] Installation Complete! You can start SpotMan using: systemctl start spotman"
