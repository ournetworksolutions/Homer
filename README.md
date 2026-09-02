<h1 align="center">Homer</h1>
<p align="center">
  <i>Advanced custom-built homelab manager and dashboard</i><br>
  <b>Homer is your only homepage you'll ever need.</b>
   <br/>
  <img width="120" src="https://raw.githubusercontent.com/ournetworksolutions/Homer/refs/heads/main/icon-192.png" />
  <br/>
</p>


## Features ⚡
- Multi-Node Web Dashboard. It runs a custom Python ThreadingHTTPServer to serve a responsive, tabbed HTML/JS interface that toggles seamlessly between internal IP and public DNS routing.
- Cross-Platform Hardware Monitoring: The script natively tracks CPU usage, RAM, network speeds, disk space, and temperatures, utilizing WMI/CIMV2 on Windows and /proc file parsing on Linux.
- Remote Service Control: Administrators can start, stop, restart, or check the status of specific services directly from the UI, executing via PowerShell on Windows or systemctl/bash scripts on Linux.
- Background Caching: A threaded loop continuously pings all configured services every 5 seconds, ensuring the web dashboard loads instantly with up-to-date statuses.
- Smart Bandwidth Throttling: It continuously polls Jellyfin; if an active video stream is detected, it automatically throttles qBittorrent by triggering its "Alternative Speed Limits". Crucially, it calculates overnight time boundaries to ensure it respects qBittorrent's built-in schedules.
- Swarm Code Synchronization: The script monitors its own file hash. If you edit the code on one machine, it automatically pushes the updated Python script to all other backend nodes and securely restarts them.
- Centralized SSL Management: It designates a "Master Node" for certificates, automatically pushing new fullchain.pem and privkey.pem files to secondary nodes so all local proxies stay secure without manual intervention.


## Getting Started 🚀

> The script tested and runs in Python 3.12.7 and 3.14.3 cross platform Windows, Linux

### Installation 🔨

Run install.sh for Linux

```bash
chmod +x install.sh && ./install.sh
```

Or for Windows, Run as administrator the install.bat file

```bash
install.bat
```

You need to have python installed.

> Once you've got Homer running, visit.

```bash
http://YOUR_SERVER_IP:8081/YOUR_SECRET_URL_PATH
```

### Supported and Tested Docker Services 🐳

- Tailscale VPN
- AdGuard Home DNS
- Nginx Proxy
- Duplicati Backups
- FileBrowser
- Jellyfin
- Navidrome
- qBitorrent
- Seerr
- Prowlarr
- Radarr
- Sonarr
- Wizarr
- Music Grabber
- Vaultwarden
- SearXNG
- Portainer
- Speedtest-Tracker
- Ngrok Tunnel
- Project Zomboid Dedicated Server
- Much more...

## Configuring 🔧

> The config is inside homer.py file. Basic json configuration for each node server.

## Shortcuts 🔎

> Desktop folder contains linux desktop shortcuts for your node servers, for fast access. Need to be configured.

## Support Our Work ❤️

> Consider buying us a coffee this month to help keep everything running. Thank you for your support!

**[☕ Coffee](https://ko-fi.com/ournetworksolutions)**


### Code and license 📜
License: GPL-3.0+/MIT
