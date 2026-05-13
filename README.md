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
- **Real-Time Telemetry**: Live websocket streams monitoring bandwidth usage and active connected clients every 2 seconds.
- **Hardware-Level Traffic Shaping**: Uses Hierarchical Token Buckets (`htb`) and `tc` IP filtering to apply per-client download bandwidth limits dynamically based on MAC address.
- **Instant Client Deauthentication**: Native `iw` bindings drop malicious connections instantly. Banning a device via the UI triggers immediate deauthentication.
- **DNS Sinkhole**: Custom domain blocking via `dnsmasq` `addn-hosts` file. New block entries take effect on `SIGHUP` (`systemctl reload dnsmasq`) — no full restart required. Intercepted queries resolve to a captive portal splash page.
- **Advanced Kernel Routing**: Automated MASQUERADE NAT providing captive portal foundations and internet sharing over the WAN interface.
- **Encrypted Authentication**: End-to-end `PyJWT` + `bcrypt` backend security locking down all critical API commands.
- **User Credential Management**: Change your password via the Settings tab. The current password must be verified before the new one is set.
- **Clean Shutdown**: Full iptables cleanup, IP forwarding reset, interface IP flush, and NetworkManager handback on hotspot stop. Leaves the system in its original state.

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

3. **Start the hotspot service:**
   ```bash
   sudo systemctl start spotman
   ```

4. **Open the web UI:**
   ```
   http://localhost:5173
   ```

5. **Login** with any credentials (first login creates the admin account) — **Username**: `admin`, **Password**: `admin`. Change immediately after login.

## 📖 Documentation

Full documentation is available in the `docs/` folder. Start with [docs/index.md](docs/index.md).

**Quick links:**
- [Quick Start & Architecture](docs/index.md#quick-start)
- [First Login & Credential Change](docs/index.md#first-login--credential-change)
- [Hotspot Management](docs/index.md#hotspot-management)
- [Device Management](docs/index.md#device-management)
- [DNS Sinkhole](docs/index.md#dns-sinkhole)
- [Traffic Shaping](docs/index.md#traffic-shaping)
- [API Reference](docs/index.md#api-reference)
- [Troubleshooting](docs/index.md#troubleshooting)

## 🔧 Hotspot Lifecycle

**Start sequence:**
1. NetworkManager releases the wLAN interface (`nmcli device set wlan managed no`)
2. Static IP `10.0.0.1/24` assigned to wLAN
3. `hostapd.conf` and `dnsmasq.conf` rendered from templates and copied to `/etc/`
4. `hostapd` and `dnsmasq` started
5. Readiness polling confirms both services are `active` (up to 10 retries × 0.5s)
6. NAT iptables rules applied (existing rules flushed first)
7. Traffic shaping initialized (`tc` HTB root qdisc on wLAN)

**Stop sequence:**
1. `hostapd` and `dnsmasq` stopped
2. NAT iptables rules flushed (POSTROUTING + FORWARD)
3. `net.ipv4.ip_forward` reset to `0`
4. Static IP flushed from wLAN interface
5. NetworkManager regains control of wLAN
6. `tc` root qdisc removed

## ⚠️ Limitations
- **OS Dependency**: Designed for Debian/Ubuntu with `systemd` and `apt`. Other distros require adjustments to `install.sh`.
- **Interface Detection**: Auto-detects WAN via default route and wLAN via `/sys/class/net/*/wireless`. Falls back to `eth0`/`wlan0`.
- **Bandwidth Shaping**: Currently enforces **download (RX) only**. Upload (TX) shaping is planned.
- **Database**: SQLite for localized storage. For enterprise scale with thousands of concurrent authentications, consider migrating to PostgreSQL.

## 👨‍💻 Author
**Uzair Mughal**
- 🌐 **Website**: [uzair.is-a.dev](https://uzair.is-a.dev)
- 🐙 **GitHub**: [@uzairdeveloper223](https://github.com/uzairdeveloper223)
- ✉️ **Email**: contact@uzair.is-a.dev

## 📄 License

See [LICENSE](LICENSE)