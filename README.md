<div align="center">
  <img src="frontend/public/favicon.svg" alt="SpotMan Logo" width="120" />
  <h1>SpotMan Control Panel</h1>
  <h2><p align="center">WORK IN PROGRESS</p></h2>
  <p><strong>A Production-Grade ISP-level Linux Hotspot & Traffic Management System</strong></p>

  <p>
    <a href="https://github.com/uzairdeveloper223/SpotMan/issues"><img src="https://img.shields.io/github/issues/uzairdeveloper223/SpotMan" alt="Issues"/></a>
    <a href="https://github.com/uzairdeveloper223/SpotMan/pulls"><img src="https://img.shields.io/github/issues-pr/uzairdeveloper223/SpotMan" alt="Pull Requests"/></a>
    <a href="https://github.com/uzairdeveloper223/SpotMan/stargazers"><img src="https://img.shields.io/github/stars/uzairdeveloper223/SpotMan" alt="Stars"/></a>
    <a href="https://github.com/uzairdeveloper223/SpotMan/network/members"><img src="https://img.shields.io/github/forks/uzairdeveloper223/SpotMan" alt="Forks"/></a>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"/>
  </p>
</div>

<br />

## 📡 Overview
SpotMan is a comprehensive, asynchronous API and React-driven control panel built for Linux. It acts as an ISP-level gateway, allowing administrators to natively deploy, shape, and monitor wireless environments. Utilizing low-level Linux utilities (`hostapd`, `dnsmasq`, `tc`, `iptables`, `iw`), SpotMan guarantees high-performance routing with an elegant, modern web interface.

## ✨ Features
- **Real-Time Telemetry**: Live websocket streams monitoring bandwidth and active endpoints.
- **Hardware-Level Traffic Shaping**: Uses Hierarchical Token Buckets (`htb`) and `tc` IP filtering to apply strict upload/download throttles dynamically per MAC address.
- **Instant Client Deauthentication**: Native `iw` bindings drop malicious connections instantly without rebooting the access point.
- **DNS Sinkhole**: Custom domain blocking with `dnsmasq` `addn-hosts` override, intercepting queries and routing them to a custom Nginx splash page. SIGHUP reloads block rules without service restart.
- **Advanced Kernel Routing**: Automated MASQUERADE NAT providing captive portal foundations and internet sharing.
- **Encrypted Authentication**: End-to-end `PyJWT` backend security locking down all critical commands.
- **Clean Shutdown**: Full iptables cleanup, IP forwarding reset, interface IP flush, and NetworkManager handback on hotspot stop.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/uzairdeveloper223/SpotMan.git
   cd SpotMan
   ```

2. **Run the installer script:** (Requires Root)
   ```bash
   sudo ./scripts/install.sh
   ```
   *This automatically sets up `sudoers` rules, Nginx templates, installs OS dependencies (`hostapd`, `dnsmasq`, `iw`, `iproute2`, `iptables`, `sqlite3`, `python3-venv`), creates the empty `custom_blocks.conf`, and configures the default hostapd path.*

3. **Start the Development Server:**
   ```bash
   ./scripts/start-dev.sh
   ```
   *The React UI will run on `http://localhost:5173` and the FastAPI backend on `http://localhost:8000`.*

## 🔑 Login
By default, the SQLite database is bootstrapped with the following administrative credentials:
- **Username**: `admin`
- **Password**: `admin`

*Note: Please change these credentials or manually modify the `users` SQLite table before rolling out to production.*

## 🔧 DNS Sinkhole How It Works
1. Blocked domains are written to `backend/config/custom_blocks.conf` in hosts-file format (`10.0.0.1 example.com`).
2. The dnsmasq template uses `addn-hosts=` to load this file — `SIGHUP` (via `systemctl reload dnsmasq`) picks up changes without a full restart.
3. Traffic to blocked domains resolves to the sinkhole IP (default `10.0.0.1`), which Nginx serves a custom block page from.

## 🛠️ Hotspot Lifecycle
- **Start**: NetworkManager releases the wLAN interface → static IP assigned → hostapd + dnsmasq started → readiness verified via polling → NAT iptables rules applied (flushed first) → traffic shaping (tc HTB) initialized.
- **Stop**: hostapd + dnsmasq stopped → iptables POSTROUTING/FORWARD flushed → `ip_forward` reset to 0 → wLAN IP flushed → NetworkManager regains control → tc root qdisc removed.

## ⚠️ Limitations
- **OS Dependency**: Highly tailored for Debian/Ubuntu environments relying heavily on `systemd` and `apt` availability.
- **Interface Naming**: Currently auto-detects WAN and wLAN interfaces via default route and `/sys/class/net`. For custom network interfaces, core configuration template overrides are required.
- **Concurrency**: SQLite is utilized for localized storage; for massive enterprise scales handling thousands of parallel authentications, migrating `database.py` to PostgreSQL is recommended.

## 👨‍💻 Author
**Uzair Mughal**
- 🌐 **Website**: [uzair.is-a.dev](https://uzair.is-a.dev)
- 🐙 **GitHub**: [@uzairdeveloper223](https://github.com/uzairdeveloper223)
- ✉️ **Email**: contact@uzair.is-a.dev

## 📄 License
This project is licensed under the MIT License.