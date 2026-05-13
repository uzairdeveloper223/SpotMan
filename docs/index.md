# SpotMan — Complete Documentation

> **SpotMan** is an ISP-level Linux hotspot and traffic management system built with FastAPI, React, and low-level Linux networking tools.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [First Login & Credential Change](#first-login--credential-change)
- [Dashboard](#dashboard)
- [Hotspot Management](#hotspot-management)
- [Device Management](#device-management)
- [DNS Sinkhole](#dns-sinkhole)
- [Traffic Shaping](#traffic-shaping)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## Quick Start

```bash
git clone https://github.com/uzairdeveloper223/SpotMan.git
cd SpotMan
sudo ./scripts/install.sh
sudo systemctl start spotman
```

Open `http://localhost:5173` in your browser. Log in with any username/password (first login creates the admin account).

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React)                    │
│  http://localhost:5173                              │
├─────────────────────────────────────────────────────┤
│                  Backend (FastAPI)                   │
│  http://localhost:8000                              │
│  ├── /api/v1/auth        — JWT auth + credentials   │
│  ├── /api/v1/hotspot     — start/stop/status        │
│  ├── /api/v1/devices     — connected clients        │
│  ├── /api/v1/traffic     — bandwidth logs & export   │
│  ├── /api/v1/dns         — DNS sinkhole rules        │
│  └── /ws                 — WebSocket telemetry       │
├─────────────────────────────────────────────────────┤
│                  System Services                     │
│  hostapd  — WiFi access point daemon                │
│  dnsmasq  — DHCP + DNS + domain blocking            │
│  nginx    — captive portal / block page             │
│  tc       — traffic shaping (HTB qdisc)             │
│  iptables — NAT / MASQUERADE routing                │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Debian/Ubuntu-based Linux
- Root or sudo access
- A wireless interface (wLAN) and a wired/WAN interface

### Running the Installer

```bash
sudo ./scripts/install.sh
```

This script:
1. Copies Nginx site configuration for the captive portal
2. Installs the SpotMan systemd service (`/etc/systemd/system/spotman.service`)
3. Creates sudoers rules for passwordless access to `hostapd`, `dnsmasq`, `iptables`, `tc`, `nmcli`, `sysctl`, `ip`, `iw`
4. Installs dependencies: `hostapd dnsmasq nginx iw iproute2 iptables sqlite3 python3-venv`
5. Creates an empty `custom_blocks.conf` for DNS sinkhole rules
6. Configures hostapd default path in `/etc/default/hostapd`

### Starting and Stopping

```bash
sudo systemctl start spotman    # Start the backend + hotspot
sudo systemctl stop spotman     # Stop (full cleanup applied)
sudo systemctl status spotman   # Check status
sudo systemctl enable spotman   # Start on boot
```

---

## First Login & Credential Change

### Default Credentials

| Field    | Value  |
|----------|--------|
| Username | `admin` |
| Password | `admin` |

> ⚠️ **Change these immediately after first login.**

### Accessing Settings

After logging in, click the **Settings** tab in the navigation bar.

### Changing Your Password

1. Navigate to **Settings** → **Change Password**
2. Enter your **current password**
3. Enter and confirm your **new password** (minimum 6 characters)
4. Click **Update Password**

The old password is verified before the change is applied. If the old password is incorrect, you will receive a `401 Unauthorized` error.

### What Happens Under the Hood

When you submit the form, the frontend calls:

```
POST /api/v1/auth/change-credentials
{
  "old_password": "current_password",
  "new_password": "new_secure_password"
}
```

The backend verifies `old_password` against the bcrypt hash stored in SQLite, then hashes and stores `new_password`.

> The username is immutable — only the password can be changed. The default username is `admin`.

---

## Dashboard

The dashboard provides real-time status updated every 2 seconds via WebSocket.

| Widget         | Description                                                    |
|----------------|----------------------------------------------------------------|
| Connection     | WebSocket connection status (green = live, red = disconnected) |
| Connected      | Number of WiFi clients currently connected                     |
| Traffic (RX)   | Total bytes received across all connected devices              |
| Traffic (TX)   | Total bytes transmitted across all connected devices           |
| Hotspot Status | Active/Inactive badge with Start/Stop toggle button           |
| Service Status | Individual status of `hostapd` and `dnsmasq` (Running/Stopped) |

---

## Hotspot Management

### Starting the Hotspot

When you click **Start Network**:

1. `custom_blocks.conf` is created if missing (prevents dnsmasq crash)
2. NetworkManager releases the wLAN interface (`nmcli device set <iface> managed no`)
3. Static IP `10.0.0.1/24` is assigned to the wLAN interface
4. `hostapd.conf` and `dnsmasq.conf` are rendered from templates
5. `hostapd` and `dnsmasq` are restarted
6. A readiness check polls `is-active` for up to 5 seconds
7. NAT iptables rules are flushed, then applied (MASQUERADE + FORWARD)
8. Traffic shaping (tc HTB) is initialized on the wLAN interface

### Stopping the Hotspot

When you click **Stop Network**:

1. `hostapd` and `dnsmasq` are stopped
2. NAT iptables rules (POSTROUTING + FORWARD) are flushed
3. IP forwarding is reset to `0` (`sysctl net.ipv4.ip_forward=0`)
4. Static IP is flushed from the wLAN interface
5. NetworkManager regains control (`nmcli device set <iface> managed yes`)
6. Traffic shaping root qdisc is removed

> This ensures your laptop WiFi is fully restored to its original state after stopping the hotspot.

---

## Device Management

The **Devices** tab shows all wireless clients detected by `iw station dump`.

| Column          | Description                                                |
|-----------------|------------------------------------------------------------|
| Status          | Active (green dot) or Offline (gray dot)                  |
| Device Info     | Hostname, MAC address, IP address                          |
| Traffic         | Upload (↑) and Download (↓) per client                    |
| Last Seen       | Timestamp of last activity                                 |
| Actions         | **Ban** (disconnect + block) or **Unban** button           |

- **Ban**: Calls `iw dev <iface> station del <MAC>` and sets `is_banned=1` in the database.
- **Unban**: Removes the ban flag and clears the deauthentication.
- **Bandwidth Limits**: Can be set per-device (download only) via the `bandwidth_limit_rx` field.

### Traffic Refresh

Device data refreshes every 5 seconds via `iw station dump`.

---

## DNS Sinkhole

The DNS sinkhole blocks access to specific domains by redirecting them to the SpotMan captive portal.

### How It Works

1. Blocked domains are stored in `/opt/spotman/backend/config/custom_blocks.conf` using **hosts-file format**:
   ```
   10.0.0.1 example.com
   10.0.0.1 ads.google.com
   ```

2. The dnsmasq configuration uses `addn-hosts=` to load this file:
   ```
   addn-hosts=/opt/spotman/backend/config/custom_blocks.conf
   ```

3. When a client queries a blocked domain, dnsmasq resolves it to `10.0.0.1` (the sinkhole IP).

4. Nginx catches all requests to the sinkhole IP and serves the custom `block.html` page.

5. When rules change, `systemctl reload dnsmasq` sends `SIGHUP`, which re-reads the `addn-hosts` file — **no full restart required**.

### Adding/Removing Block Rules

1. Enter a domain (e.g., `example.com`) in the **DNS Sinkhole** tab
2. Click **Block** to add it
3. Click **Remove** next to a blocked domain to unblock it

### Blocking Rules File

```
Location: /opt/spotman/backend/config/custom_blocks.conf
Format: <sinkhole_ip> <domain>
Example: 10.0.0.1 blocked-site.com
```

> Comments (`#`) and blank lines are ignored.

---

## Traffic Shaping

Traffic shaping uses Linux `tc` with **Hierarchical Token Bucket (HTB)** queuing discipline.

### How It Works

1. A root HTB qdisc is created on the wLAN interface:
   ```
   tc qdisc add dev wlan0 root handle 1: htb default 10
   ```

2. Per-IP classes are created with rate limits:
   ```
   tc class add dev wlan0 parent 1: classid 1:100 htb rate 1024kbit
   ```

3. A Stochastic Fairness Queuing (SFQ) sub-qdisc ensures fairness within each class:
   ```
   tc qdisc add dev wlan0 parent 1:100 handle 100: sfq perturb 10
   ```

4. `u32` filters match destination IPs and route traffic into the correct class:
   ```
   tc filter add dev wlan0 parent 1: protocol ip prio 1 u32 match ip dst 10.0.0.50 flowid 1:100
   ```

### Setting Limits

1. Go to the **Devices** tab
2. Edit a device's `bandwidth_limit_rx` field (download limit in kbit/s)
3. The limit is applied via tc automatically

> **Note**: Currently only **download (RX)** limiting is implemented. Upload (TX) shaping is planned.

### Cleanup

When the hotspot stops, the root qdisc is removed:
```
tc qdisc del dev wlan0 root
```

---

## API Reference

All API endpoints require authentication (JWT Bearer token) except login.

### Authentication

| Method | Endpoint                | Description                  |
|--------|-------------------------|------------------------------|
| POST   | `/api/v1/auth/token`    | Login, get JWT token         |
| POST   | `/api/v1/auth/change-credentials` | Change current password |

**Login request:**
```
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Change password request:**
```json
POST /api/v1/auth/change-credentials
Authorization: Bearer <token>
{
  "old_password": "current_password",
  "new_password": "new_password"
}
```

### Hotspot

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | `/api/v1/hotspot`  | Get hotspot status       |
| POST   | `/api/v1/hotspot/start` | Start the hotspot    |
| POST   | `/api/v1/hotspot/stop`  | Stop the hotspot     |

### Devices

| Method | Endpoint              | Description                  |
|--------|-----------------------|------------------------------|
| GET    | `/api/v1/devices`     | List all devices             |
| GET    | `/api/v1/devices/{mac}` | Get device by MAC         |
| PATCH  | `/api/v1/devices/{mac}` | Update device (ban/limit) |

### Traffic

| Method | Endpoint                  | Description                  |
|--------|---------------------------|------------------------------|
| GET    | `/api/v1/traffic/export`  | Export traffic logs as CSV   |
| POST   | `/api/v1/traffic/prune`   | Prune old logs (default 30d) |

### DNS

| Method | Endpoint                 | Description                  |
|--------|--------------------------|------------------------------|
| GET    | `/api/v1/dns`            | Get sinkhole status + blocked domains |
| POST   | `/api/v1/dns/block`      | Block a domain               |
| POST   | `/api/v1/dns/unblock`    | Unblock a domain             |

### WebSocket

| Endpoint       | Description                       |
|----------------|-----------------------------------|
| `/ws`          | Real-time status updates (every 2s) |

**Message format:**
```json
{
  "type": "status_update",
  "payload": {
    "hotspot": { "active": true, "hostapd_active": true, "dnsmasq_active": true },
    "devices": 5,
    "traffic": { "rx_bytes": 1048576, "tx_bytes": 524288 }
  }
}
```

---

## Troubleshooting

### DNS Blocking Not Working

- Verify `custom_blocks.conf` exists and contains entries in hosts-file format:
  ```bash
  cat /opt/spotman/backend/config/custom_blocks.conf
  ```
- Verify dnsmasq config uses `addn-hosts=`:
  ```bash
  cat /etc/dnsmasq.d/spotman.conf | grep addn-hosts
  ```
- Reload dnsmasq after changes:
  ```bash
  sudo systemctl reload dnsmasq
  ```

### hostapd and NetworkManager Fighting for wLAN

- Ensure `nmcli device set <iface> managed no` runs before hostapd starts
- Check hostapd status:
  ```bash
  sudo systemctl status hostapd
  journalctl -u hostapd -n 50
  ```

### iptables Rules Stacking

- The code now flushes rules before adding. If issues persist, manually flush:
  ```bash
  sudo iptables -F FORWARD
  sudo iptables -t nat -F POSTROUTING
  ```

### dnsmasq Won't Start

- Ensure `custom_blocks.conf` exists (even if empty):
  ```bash
  sudo touch /opt/spotman/backend/config/custom_blocks.conf
  ```
- Check dnsmasq config syntax:
  ```bash
  dnsmasq --test
  ```

### Client Not Getting IP via DHCP

- Check dnsmasq is running and listening:
  ```bash
  sudo systemctl status dnsmasq
  ss -tulnp | grep :67
  ```
- Check interface has the static IP:
  ```bash
  ip addr show dev wlan0
  ```

---

## Project Structure

```
SpotMan/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI route handlers
│   │   │   ├── auth.py             # Login + password change endpoints
│   │   │   ├── devices.py          # Device listing, banning, bandwidth limits
│   │   │   ├── dns.py              # DNS sinkhole block/unblock
│   │   │   ├── hotspot.py          # Start/stop/status API
│   │   │   ├── traffic.py          # CSV export, log pruning
│   │   │   ├── websocket.py        # Real-time status broadcaster
│   │   │   └── __init__.py
│   │   ├── core/                    # Core business logic
│   │   │   ├── dns.py              # DNS block file management
│   │   │   ├── devices.py          # iw + dnsmasq lease parsing
│   │   │   ├── hotspot.py          # Service lifecycle, iptables, NM, tc
│   │   │   ├── traffic.py          # tc HTB initialization
│   │   │   └── __init__.py
│   │   ├── models/                  # Database models
│   │   │   ├── device.py           # Device model + Pydantic schemas
│   │   │   ├── database.py         # SQLite setup + db connection
│   │   │   └── __init__.py
│   │   ├── utils/                   # Utility modules
│   │   │   ├── system.py           # Async command runner (run_command)
│   │   │   ├── network.py          # Interface detection, MAC/IP validation
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── config/
│   │   ├── dnsmasq.conf.template   # dnsmasq config template
│   │   ├── hostapd.conf.template   # hostapd config template
│   │   ├── nginx.conf.template     # Nginx captive portal config
│   │   ├── custom_blocks.conf      # DNS sinkhole block list (hosts format)
│   │   └── block.html              # Captive portal block page
│   └── systemd/
│       └── spotman.service         # Systemd service unit
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── App.tsx             # Main layout + routing
│   │   │   ├── Dashboard.tsx       # Dashboard with WebSocket status
│   │   │   ├── DeviceList.tsx      # Connected devices table
│   │   │   ├── DnsConfig.tsx       # DNS sinkhole block/unblock UI
│   │   │   ├── Login.tsx           # Login form
│   │   │   └── Settings.tsx        # Account settings + password change
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts     # WebSocket connection hook
│   │   ├── main.tsx                # React entry point
│   │   └── ...
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── index.html
├── docs/
│   └── index.md                    # This documentation
├── scripts/
│   └── install.sh                  # Installation script
├── README.md                       # Overview + quick start
└── status.md                       # Fix tracking document
```