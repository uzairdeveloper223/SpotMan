# SpotMan

![SpotMan Banner](frontend/public/banner.svg)

SpotMan is a comprehensive, ISP-level control panel designed for managing and monitoring Linux-based Wi-Fi hotspots. Built for pentesters and network administrators, it provides deep visibility and absolute control over connected clients.

## Features

- Real-time Device Monitoring: Live dashboard showing MAC addresses, IP addresses, hostnames, and bandwidth usage.
- Hotspot Management: Initialize, start, and stop Wi-Fi hotspots with custom SSID, password, channel, and band (2.4GHz/5GHz) settings.
- Client Control: 
    - Disconnect specific devices.
    - Ban/Blacklist devices by MAC address.
    - Throttle internet speed per client using kernel-level Traffic Control (tc).
    - Isolate clients from the internet while maintaining local connectivity.
- Advanced Filtering:
    - DNS Sinkholing: Block domains at the network level using dnsmasq.
    - Traffic Redirection: Redirect specific domain or IP traffic to local targets.
    - Forced DNS: Ensure all clients use specified DNS servers.
- Persistence: SQLite database for logging device history, session data, and administrative actions.

## Tech Stack

- Backend: Go (Golang)
- Frontend: React + TypeScript + Tailwind CSS
- Networking: hostapd, dnsmasq, nftables, tc (iproute2)
- Database: SQLite

## Installation

### Prerequisites

- Ubuntu (22.04 LTS or newer recommended)
- Wi-Fi adapter supporting AP mode
- Root/Sudo privileges

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/uzairdeveloper223/spotman.git
   cd spotman
   ```

2. Install system dependencies:
   ```bash
   ./scripts/setup.sh
   ```

3. Build the application:
   ```bash
   make build
   ```

## Usage

1. Start the backend server:
   ```bash
   make run
   ```

2. Access the web interface at `http://localhost:8080` (or as configured in your frontend development server).

## Limitations

- Operating System: Specifically targeted and tested on Ubuntu. Compatibility with other distributions is not guaranteed without modification.
- Hardware: Requires a Wi-Fi network interface card (NIC) that supports AP (Access Point) mode. Many consumer-grade USB Wi-Fi adapters do not support this.
- Privileges: The backend must run with elevated privileges (sudo) to manipulate the Linux kernel network stack, firewall rules, and traffic control settings.
- Interference: Performance may be affected by environmental factors and physical interference on chosen Wi-Fi channels.

## About Me

**Uzair Mughal**
- GitHub: [uzairdeveloper223](https://github.com/uzairdeveloper223)
- Website: [uzair.is-a.dev](https://uzair.is-a.dev)
- Contact: contact@uzair.is-a.dev

---

Designed for speed, security, and absolute control.
