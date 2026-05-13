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
- **DNS Sinkhole**: Custom domain blocking via `dnsmasq` `addn-hosts` file. New block entries take effect on `SIGHUP` (`systemctl reload dnsmasq`) — no full restart required. Intercepted queries resolve to a local Nginx splash page.
- **Advanced Kernel Routing**: Automated MASQUERADE NAT providing captive portal foundations and internet sharing over the WAN interface.
- **Encrypted Authentication**: End-to-end `PyJWT` + `bcrypt` backend security locking down all critical API commands.
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
   *First login credentials — **Username**: `admin`, **Password**: `admin`. Please change these immediately after first login.*

4. **Start the Development Server (optional, for dev/testing):**
   ```bash
   ./scripts/start-dev.sh
   ```
   *The React UI will run on `http://localhost:5173` and the FastAPI backend on `http://localhost:8000`.*

## 🔧 DNS Sinkhole How It Works
1. Blocked domains are written to `backend/config/custom_blocks.conf` in hosts-file format: `10.0.0.1 example.com`.
2. The dnsmasq template uses `addn-hosts=` to load this file. Sending `SIGHUP` via `systemctl reload dnsmasq` re-reads the file — no full restart needed.
3. Traffic to blocked domains resolves to the sinkhole IP (`10.0.0.1` by default), which Nginx serves a custom block page from.

## 🛠️ Hotspot Lifecycle

**Start sequence:**
1. NetworkManager releases the wLAN interface (`nmcli device set wlan managed no`)
2. Static IP `10.0.0.1/24` assigned to the wLAN interface
3. `hostapd.conf` and `dnsmasq.conf` rendered from templates and copied to `/etc/`
4. `hostapd` and `dnsmasq` restarted
5. Readiness polling confirms both services are `active` (up to 10 × 0.5s)
6. NAT iptables rules applied (existing POSTROUTING/FORWARD flushed first)
7. Traffic shaping initialized (`tc` HTB root qdisc on wLAN)

**Stop sequence:**
1. `hostapd` and `dnsmasq` stopped
2. NAT iptables rules flushed (POSTROUTING + FORWARD)
3. `net.ipv4.ip_forward` reset to `0`
4. Static IP flushed from wLAN interface
5. NetworkManager regains control of wLAN (`nmcli device set wlan managed yes`)
6. `tc` root qdisc removed from wLAN

## ⚠️ Limitations
- **OS Dependency**: Designed for Debian/Ubuntu environments with `systemd` and `apt`. Other distributions may require adjustments to `install.sh` and service paths.
- **Interface Detection**: WAN and wLAN interfaces are auto-detected via default route and `/sys/class/net/*/wireless`. Falls back to `eth0`/`wlan0` if detection fails. For non-standard setups, edit the detection functions in `utils/network.py`.
- **Bandwidth Shaping**: Currently enforces download (RX) limits only. Upload (TX) shaping is not yet implemented despite having database fields for it.
- **Database**: Uses SQLite for localized storage. For enterprise deployments handling thousands of concurrent authentications, migrating `models/database.py` to PostgreSQL is recommended.

## 📂 Project Structure
```
SpotMan/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI route handlers
│   │   ├── core/                   # Core logic (hotspot, dns, traffic, devices)
│   │   ├── models/                 # Database models & connection
│   │   └── utils/                  # System commands & network helpers
│   ├── config/                     # Templates (dnsmasq, hostapd, nginx, block page)
│   └── systemd/                    # SpotMan systemd service unit
├── frontend/                       # React UI (Vite)
└── scripts/                        # install.sh
```

## 👨‍💻 Author
**Uzair Mughal**
- 🌐 **Website**: [uzair.is-a.dev](https://uzair.is-a.dev)
- 🐙 **GitHub**: [@uzairdeveloper223](https://github.com/uzairdeveloper223)
- ✉️ **Email**: contact@uzair.is-a.dev

## 📄 License
This project is licensed under the MIT License.