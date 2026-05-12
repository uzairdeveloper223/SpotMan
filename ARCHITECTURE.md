# SpotMan Technical Architecture & Project Status

This document provides a comprehensive overview of the SpotMan architecture, current implementation status, and future roadmap.

## 1. System Architecture

SpotMan is designed as a lightweight, high-performance network management suite for Linux (Ubuntu). It follows a decoupled architecture:

### 1.1 Backend (Go)
- **Role**: High-privilege controller for the Linux network stack.
- **Components**:
    - **API Layer**: `net/http` based REST endpoints and WebSockets for real-time data.
    - **Network Layer**: Wrappers for `nftables` (routing/firewall), `tc` (traffic control), `hostapd` (Wi-Fi AP), and `dnsmasq` (DHCP/DNS).
    - **Monitor Layer**: Polls kernel interfaces (`/proc/net/arp`) and nftables counters for live device and bandwidth tracking.
    - **Persistence Layer**: SQLite for logging system events and device usage history.
- **Security**: Commands are executed via a dedicated `SudoRunner` using argument arrays to prevent shell injection.

### 1.2 Frontend (React + TS)
- **Role**: Modern, tool-based UI for real-time management.
- **Tech Stack**: Vite, Tailwind CSS v4, TypeScript.
- **Communication**: Communicates with the backend via a reverse proxy (Vite dev server) or direct production port, utilizing WebSockets for live dashboard updates.

---

## 2. Implementation Status (What is Made)

### 2.1 Hotspot Management
- [x] Hostapd configuration generation (WPA2-PSK).
- [x] Dnsmasq integration for DHCP and DNS.
- [x] Dynamic network interface detection and selection.
- [x] Automated IP forwarding and NAT setup via nftables.

### 2.2 Device Monitoring
- [x] Real-time device discovery via ARP table polling.
- [x] Live bandwidth monitoring (Upload/Download) using nftables packet counters.
- [x] Real-time UI updates via WebSockets.

### 2.3 Network Control (Pentester Features)
- [x] MAC-based device banning.
- [x] Per-IP bandwidth throttling using kernel `tc`.
- [x] DNS Sinkholing for domain blocking.
- [x] Custom "Access Denied" landing page for blocked traffic.

### 2.4 Data & Logging
- [x] SQLite database schema for devices and logs.
- [x] Log export functionality (CSV and JSON formats).
- [x] System action logging (Start/Stop/Ban events).

---

## 3. Remaining Tasks & Roadmap

While the core functionality is complete, the following features are planned for future versions:

### 3.1 Advanced Interception (Roadmap)
- [ ] **Packet Capture**: Trigger per-device PCAP recording using `tcpdump` integration.
- [ ] **MITM Integration**: Transparent proxying via `mitmproxy` or `bettercap`.
- [ ] **Captive Portal**: Custom authentication flow for open hotspots.

### 3.2 UI/UX Enhancements
- [ ] **Historical Graphs**: Visualizing bandwidth usage over time using Chart.js.
- [ ] **Mobile Optimization**: Responsive layout refinements for phone-based management.
- [ ] **Theming**: Toggle between dark and light modes.

### 3.3 Security & Robustness
- [ ] **Linux Capabilities**: Transition from raw `sudo` to specific `setcap` capabilities (CAP_NET_ADMIN, CAP_NET_RAW) for the backend binary.
- [ ] **Multi-Distro Support**: Testing and abstraction for Arch, Fedora, and RHEL-based systems.

---

## 4. Architecture Diagram (Logical)

```text
[ User Browser ] <---(WS/HTTP)---> [ Go Backend ]
                                       |
                                       +---(Process)---> [ hostapd ]
                                       +---(Process)---> [ dnsmasq ]
                                       +---(Syscall)---> [ nftables ]
                                       +---(Syscall)---> [ Traffic Control ]
                                       +---(File IO)---> [ /proc/net/arp ]
                                       +---(File IO)---> [ spotman.db ]
```

---

**Author**: Uzair Mughal
**Repository**: [github.com/uzairdeveloper223/spotman](https://github.com/uzairdeveloper223/spotman)
