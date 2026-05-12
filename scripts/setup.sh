#!/usr/bin/env bash
set -euo pipefail

echo "Installing system dependencies for SpotMan..."

sudo apt update
sudo apt install -y \
    hostapd \
    dnsmasq \
    nftables \
    iproute2 \
    iw \
    rfkill \
    build-essential

echo "Dependencies installed."
