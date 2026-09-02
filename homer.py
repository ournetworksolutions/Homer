#!/usr/bin/python
import socket
import json
import os
import re
import time
import concurrent.futures
import urllib.request
import urllib.parse
import ssl
import hashlib
import random
import string
import gzip
import subprocess
import shlex
import threading
import platform
import shutil
import sys
import ast
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ==========================================
# 1. GLOBAL SECRETS & CROSS-PLATFORM SETUP
# ==========================================
IS_LINUX = platform.system() != "Windows"

# Setup for Swarm Auto-Sync & Restart
SCRIPT_PATH = os.path.abspath(__file__)
try:
    SCRIPT_HASH = hashlib.md5(open(SCRIPT_PATH, 'rb').read()).hexdigest()
except Exception:
    SCRIPT_HASH = ""

def restart_script():
    print("Restarting Homer Swarm Node...")
    os.execv(sys.executable, [sys.executable, SCRIPT_PATH])

# Global variable to hold the dynamically detected certificate path & node ID
ACTIVE_CERT = ""
LOCAL_NODE_ID = "main"

NET = {
    "PORT": 8081,
    "MAIN_SERVER": "10.10.10.10",
    "MAIN_ROUTER": "10.10.10.1",
    "MAIN_SWITCH": "10.10.10.2",
    "GAMEBOX_ROUTER": "10.10.10.254",
    "GAMEBOX_SERVER": "10.10.10.13"
}

SETTINGS = {
    "CONTAINERS_NUMBER": "28",
    "REBOOT_PASSWORD": "0",
    "REBOOT_COMMAND": "reboot" if IS_LINUX else "shutdown /r /t 0", 
    "DOCKERS_FOLDER": "/home/main/Documents/Homer/dockers/" if IS_LINUX else "C:\\dockers\\", 
    "SECRET_URL_PATH": "/RANDOM_KEY_FOR_URL",
    "MAINTENANCE_FOLDER": "/home/main/Documents/Homer/Maintenance/" if IS_LINUX else "C:\\maintenance\\"
}

ALWAYS_ONLINE = ["Router Gateway", "MikroTik Switch", "Cloud Gateway", "Jellyfin Gateway", "Navidrome Gateway"]

# ==========================================
# 2. DASHBOARD CONFIGURATION (SWARM PEERS)
# ==========================================
GATEWAY_CONFIG = {
    "Cloud Gateway": [
        { "title": "Cloud for Users", "url": "https://EXAMPLE_URL" },
        { "title": "Backup for Administrators", "url": "https://EXAMPLE_URL" }
    ],
    "Jellyfin Gateway": [
        { "title": "Jellyfin for Users", "url": "https://EXAMPLE_URL" },
        { "title": "Backup for Administrators", "url": "https://EXAMPLE_URL" }
    ],
    "Navidrome Gateway": [
        { "title": "Navidrome for Users", "url": "https://EXAMPLE_URL" },
        { "title": "Backup for Administrators", "url": "https://EXAMPLE_URL" }
    ]
}

DASHBOARD_CONFIG = [
    {
        "id": "main", # Node ID
        "title": "Main Node", # Node Name
        "mode": "backend", # (static|backend) backend is for have a managed node server, while static is a simple dashboard for services without be able to interact with them.
        "enable_auto_throttle": True, # If True, it monitors Jellyfin for video playback and dynamically throttles qBittorrent download speeds (Alternative Speed) across your network to prevent buffering.
        "is_cert_master": True, # Certificates Master Node. All other Node servers will receive certs from this node.
        "bind_ip": f"{NET['MAIN_SERVER']}", # Node IP that Homer will try to bind automatically
        "cert_path": "/root/.local/share/mkcert/rootCA.pem", # Node Certificates Path for install in your devices if self signed Certificates.
        "sync_certs_dir": "/home/main/Documents/Homer/dockers/nginx/data/custom_ssl/npm-1", # Node Certificates Path sync between other Nodes.
        "domain_names": [f"{NET['MAIN_SERVER']}", "homer.dashboard.com", "localhost", "127.0.0.1"], # All the URL's the Node server has.
        "api_ip": f"http://{NET['MAIN_SERVER']}:{NET['PORT']}{SETTINGS['SECRET_URL_PATH']}", # Full Node IP URL
        "api_dns": f"http://homer.dashboard.com", # Node domain name
        "color": "#00ff99", # Node services color
        "allow_controls": True, # Node control (start|stop|restart)
        "keys": { # API keys and credentials
            "JELLYFIN": "API_KEY_PLACE_HERE",
            #"SEERR": "API_KEY_PLACE_HERE", # One ARR Stack Seerr Service instance.
            "SEERR_1": "API_KEY_PLACE_HERE", # Double ARR Stack Seerr Service instances.
            "SEERR_2": "API_KEY_PLACE_HERE", # Double ARR Stack Seerr Service instances.
            "PORTAINER": "API_KEY_PLACE_HERE",
            "ADGUARD_USER": "ADGUARD_USERNAME_PLACE_HERE",
            "ADGUARD_PASS": "ADGUARD_PASSWORD_PLACE_HERE",
            "NAVIDROME_USER": "NAVIDROME_USERNAME_PLACE_HERE",
            "NAVIDROME_PASS": "NAVIDROME_PASSWORD_PLACE_HERE",
            "VUETORRENT_USER": "VUETORRENT_USERNAME_PLACE_HERE",
            "VUETORRENT_PASS": "VUETORRENT_PASSWORD_PLACE_HERE"
        },
        "items": [ # Services names, domain names, ips:ports, path for script that will (start|stop|restart) service, comment of service
            {"name": "Router Gateway", "local": f"https://router.homer.com", "public": f"http://{NET['MAIN_ROUTER']}", "script_dir": SETTINGS['MAINTENANCE_FOLDER']+"router"},
            {"name": "MikroTik Switch", "local": f"https://switch.homer.com", "public": f"http://{NET['MAIN_SWITCH']}", "script_dir": SETTINGS['MAINTENANCE_FOLDER']+"switch"},
            {"name": "Tailscale VPN", "local": "https://login.tailscale.com/admin/machines", "public": "https://login.tailscale.com/admin/machines", "script_dir": SETTINGS['DOCKERS_FOLDER']+"tailscale"},
            {"name": "Maintenance", "local": f"http://maintenance.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8384"},
            {"name": "AdGuard Home DNS", "local": f"https://adguard.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8485", "script_dir": SETTINGS['DOCKERS_FOLDER']+"adguard"},
            {"name": "Nginx Proxy", "local": f"https://nginx.homer.com", "public": f"http://{NET['MAIN_SERVER']}:81", "script_dir": SETTINGS['DOCKERS_FOLDER']+"nginx"},
            {"name": "Duplicati Backup", "local": f"https://duplicati.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8200", "script_dir": SETTINGS['DOCKERS_FOLDER']+"duplicati", "comment": "Server is GameBox"},
            {"name": "Cloud Gateway", "local": f"", "public": f"http://{NET['MAIN_SERVER']}:8182", "script_dir": SETTINGS['DOCKERS_FOLDER']+"filebrowser"},
            {"name": "Jellyfin Gateway", "local": f"", "public": f"http://{NET['MAIN_SERVER']}:8080"},
            {"name": "Navidrome Gateway", "local": f"", "public": f"http://{NET['MAIN_SERVER']}:8181"},
            {"name": "Jellyfin", "local": f"https://jellyfin.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8096", "script_dir": SETTINGS['DOCKERS_FOLDER']+"jellyfin", "comment": "Server is GameBox"},
            {"name": "VueTorrentRR", "local": f"https://vuetorrentrr.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8283", "script_dir": SETTINGS['DOCKERS_FOLDER']+"vuetorrentrr", "comment": "Server is GameBox"},
            {"name": "Seerr Source 1", "local": f"https://seerr.homer.com", "public": f"http://{NET['MAIN_SERVER']}:5055", "script_dir": SETTINGS['DOCKERS_FOLDER']+"seer_source1"},
            {"name": "Prowlarr Source 1", "local": f"https://prowlarr.homer.com", "public": f"http://{NET['MAIN_SERVER']}:9696", "script_dir": SETTINGS['DOCKERS_FOLDER']+"prowlarr_source1", "comment": "Warp Proxy: socks5://warp:1080"},
            {"name": "Radarr Source 1", "local": f"https://radarr.homer.com", "public": f"http://{NET['MAIN_SERVER']}:7878", "script_dir": SETTINGS['DOCKERS_FOLDER']+"radarr_source1"},
            {"name": "Sonarr Source 1", "local": f"https://sonarr.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8989", "script_dir": SETTINGS['DOCKERS_FOLDER']+"sonarr_source1"},
            {"name": "Seerr Source 2", "local": f"https://seerr2.homer.com", "public": f"http://{NET['MAIN_SERVER']}:5156", "script_dir": SETTINGS['DOCKERS_FOLDER']+"seer_source2"},
            {"name": "Prowlarr Source 2", "local": f"https://prowlarr2.homer.com", "public": f"http://{NET['MAIN_SERVER']}:9797", "script_dir": SETTINGS['DOCKERS_FOLDER']+"prowlarr_source2"},
            {"name": "Radarr Source 2", "local": f"https://radarr2.homer.com", "public": f"http://{NET['MAIN_SERVER']}:7979", "script_dir": SETTINGS['DOCKERS_FOLDER']+"radarr_source2"},
            {"name": "Sonarr Source 2", "local": f"https://sonarr2.homer.com", "public": f"http://{NET['MAIN_SERVER']}:9898", "script_dir": SETTINGS['DOCKERS_FOLDER']+"sonarr_source2"},
            {"name": "Wizarr", "local": f"http://wizarr.media.com", "public": f"http://{NET['MAIN_SERVER']}:5690", "script_dir": SETTINGS['DOCKERS_FOLDER']+"wizarr"},
            {"name": "Navidrome", "local": f"https://navidrome.homer.com", "public": f"http://{NET['MAIN_SERVER']}:4533", "script_dir": SETTINGS['DOCKERS_FOLDER']+"navidrome"},
            {"name": "Music Grabber", "local": f"http://musicgrabber.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8586", "script_dir": SETTINGS['DOCKERS_FOLDER']+"musicgrabber"},
            {"name": "VueTorrent", "local": f"https://vuetorrent.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8283", "script_dir": SETTINGS['DOCKERS_FOLDER']+"qbittorrent"},
            {"name": "Vaultwarden", "local": f"https://vaultwarden.homer.com", "public": f"https://{NET['MAIN_SERVER']}:8687", "script_dir": SETTINGS['DOCKERS_FOLDER']+"vaultwarden"},
            {"name": "SearXNG", "local": f"https://searxng.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8788", "script_dir": SETTINGS['DOCKERS_FOLDER']+"searxng"},
            {"name": "Portainer", "local": f"https://portainer.homer.com", "public": f"https://{NET['MAIN_SERVER']}:9443", "script_dir": SETTINGS['DOCKERS_FOLDER']+"portainer"},
            {"name": "Speedtest", "local": f"http://speedtest.homer.com", "public": f"http://{NET['MAIN_SERVER']}:8765", "script_dir": SETTINGS['DOCKERS_FOLDER']+"speedtest-tracker"},
            {"name": "ngrok tunnel", "local": f"http://ngrok.homer.com/status", "public": f"http://{NET['MAIN_SERVER']}:4040/status", "script_dir": SETTINGS['DOCKERS_FOLDER']+"ngrok"}
            {"name": "Project Zomboid", "local": f"https://pzserver.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:3001", "script_dir": SETTINGS['DOCKERS_FOLDER']+"pzserver", "comment": "Server is GameBox"}
        ]
    },
    {
        "id": "gamebox", # Node ID
        "title": "GameBox Node", # Node Name
        "mode": "backend", # (static|backend) backend is for have a managed node server, while static is a simple dashboard for services without be able to interact with them.
        "enable_auto_throttle": True, # If True, it monitors Jellyfin for video playback and dynamically throttles qBittorrent download speeds (Alternative Speed) across your network to prevent buffering.
        "bind_ip": f"{NET['GAMEBOX_SERVER']}", # Node IP that Homer will try to bind automatically
        "cert_path": "C:\\Homer\\rootCA.pem", # Node Certificates Path for install in your devices if self signed Certificates.
        "sync_certs_dir": "C:\\Users\\gamebox\\Documents\\Caddy\\certs", # Node Certificates Path sync between other Nodes.
        "domain_names": [f"{NET['GAMEBOX_SERVER']}", "homer2.dashboard.com", "localhost", "127.0.0.1"], # All the URL's the Node server has.
        "api_ip": f"http://{NET['GAMEBOX_SERVER']}:{NET['PORT']}{SETTINGS['SECRET_URL_PATH']}", # Full Node IP URL
        "api_dns": f"http://homer2.dashboard.com",
        "color": "#00ff99", # Node services color 
        "allow_controls": False, # Node control (start|stop|restart)
        "keys": { # API keys and credentials
            "JELLYFIN": "API_KEY_PLACE_HERE",
            "ADGUARD_USER": "ADGUARD_USERNAME_PLACE_HERE",
            "ADGUARD_PASS": "ADGUARD_PASSWORD_PLACE_HERE",
            "VUETORRENT_USER": "VUETORRENT_USERNAME_PLACE_HERE",
            "VUETORRENT_PASS": "VUETORRENT_PASSWORD_PLACE_HERE"
        },
        "items": [ # Services names, domain names, ips:ports, path for script that will (start|stop|restart) service, comment of service
            {"name": "Router Gateway", "local": "https://router.homer.com", "public": f"http://{NET['GAMEBOX_ROUTER']}"},
            {"name": "AdGuard Home DNS", "local": f"https://adguard.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8485", "service_id": "AdGuardHome"},
            {"name": "Caddy Proxy", "local": f"https://caddyserver.com", "public": f"http://{NET['GAMEBOX_SERVER']}:2019"},
            {"name": "Duplicati Backup", "local": f"https://duplicati.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8200", "comment": "Server is GameBox"},
            {"name": "Jellyfin Gateway", "local": f"", "public": f"http://{NET['GAMEBOX_SERVER']}:8080"},
            {"name": "VueTorrent", "local": "https://vuetorrent.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8283", "service_id": "qbittorrent"},
            {"name": "Jellyfin", "local": "https://jellyfin.homer.com", "public": f"http://{NET['GAMEBOX_SERVER']}:8096", "service_id": "JellyfinServer"}
        ]
    }
]

# ==========================================
# 3. INTERNAL ENGINE LOGIC 
# ==========================================
ALL_SERVICES = {}
uid_counter = 0
for group in DASHBOARD_CONFIG:
    for item in group["items"]:
        item["uid"] = f"svc_{uid_counter}"
        item["_node_id"] = group["id"]
        item["_node_bind_ip"] = group.get("bind_ip", "127.0.0.1")
        item["_group_mode"] = group["mode"]
        item["_group_color"] = group.get("color", "#00ff99")
        item["_group_controls"] = group.get("allow_controls", False)
        item["_keys"] = group.get("keys", {})
        ALL_SERVICES[item["uid"]] = item
        uid_counter += 1

class SystemMonitor:
    def __init__(self):
        self.last_cpu_total, self.last_cpu_idle, self.last_net_time, self.last_rx, self.last_tx = 0, 0, 0, 0, 0
        self.is_linux = IS_LINUX

    def format_speed(self, bps):
        if bps < 1024: return f"{bps:.0f} B/s"
        elif bps < 1048576: return f"{bps/1024:.1f} KB/s"
        elif bps < 1073741824: return f"{bps/1048576:.1f} MB/s"
        return f"{bps/1073741824:.1f} GB/s"

    def get_sys_info(self):
        info = {"cpu_usage": "N/A", "ram_usage": "N/A", "temp_cpu": "N/A", "net_down": "0 B/s", "net_up": "0 B/s", "uptime": "N/A"}
        
        if not self.is_linux:
            info["uptime"] = "N/A (Windows)"
            try:
                import ctypes
                millis = ctypes.windll.kernel32.GetTickCount64()
                sec = millis / 1000.0
                d, h, m = int(sec // 86400), int((sec % 86400) // 3600), int((sec % 3600) // 60)
                info["uptime"] = f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m"
            except Exception: pass
            
            try:
                c = os.popen("wmic cpu get loadpercentage").read().split()
                if len(c) > 1: info["cpu_usage"] = f"{c[1]}%"
                mt = os.popen("wmic OS get TotalVisibleMemorySize").read().split()
                mf = os.popen("wmic OS get FreePhysicalMemory").read().split()
                if len(mt) > 1 and len(mf) > 1:
                    info["ram_usage"] = f"{((int(mt[1]) - int(mf[1])) / int(mt[1])) * 100:.1f}%"
            except Exception: pass
            
            try:
                # 1. Try LibreHardwareMonitor or OpenHardwareMonitor first (Most accurate)
                hw_out = os.popen('wmic /namespace:\\\\root\\LibreHardwareMonitor PATH Sensor WHERE "SensorType=\'Temperature\' AND Name LIKE \'%CPU Package%\'" get Value 2>nul').read().split()
                if len(hw_out) < 2:
                    hw_out = os.popen('wmic /namespace:\\\\root\\OpenHardwareMonitor PATH Sensor WHERE "SensorType=\'Temperature\' AND Name LIKE \'%CPU Package%\'" get Value 2>nul').read().split()
                
                if len(hw_out) > 1 and hw_out[1].replace('.', '', 1).isdigit():
                    info["temp_cpu"] = f"{float(hw_out[1]):.1f}°C"
                else:
                    # 2. Try modern Windows CIMV2 Counters (Does not require Admin)
                    cim_out = os.popen("wmic path Win32_PerfFormattedData_Counters_ThermalZoneInformation get HighPrecisionTemperature 2>nul").read().split()
                    if len(cim_out) > 1 and cim_out[1].isdigit():
                        celsius = (int(cim_out[1]) / 10.0) - 273.15
                        # Filter out the fake motherboard placeholder values (0C and 27.9C)
                        if celsius > 5.0 and round(celsius, 1) not in [27.8, 27.9, 28.0]:
                            info["temp_cpu"] = f"{celsius:.1f}°C"
                    
                    # 3. Fallback to old ACPI method (Requires Admin)
                    if info["temp_cpu"] == "N/A":
                        tm_out = os.popen("wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature 2>nul").read().split()
                        if len(tm_out) > 1 and tm_out[1].isdigit():
                            celsius = (int(tm_out[1]) / 10.0) - 273.15
                            if celsius > 5.0 and round(celsius, 1) not in [27.8, 27.9, 28.0]:
                                info["temp_cpu"] = f"{celsius:.1f}°C"
            except Exception: pass
            
            try:
                now = time.time()
                for line in os.popen("netstat -e").read().split('\n'):
                    if line.strip().startswith("Bytes"):
                        parts = line.split()
                        if len(parts) >= 3:
                            rx, tx = int(parts[1]), int(parts[2])
                            if self.last_net_time > 0 and (now - self.last_net_time) > 0:
                                el = now - self.last_net_time
                                if rx >= self.last_rx: info["net_down"] = self.format_speed((rx - self.last_rx) / el)
                                if tx >= self.last_tx: info["net_up"] = self.format_speed((tx - self.last_tx) / el)
                            self.last_rx, self.last_tx, self.last_net_time = rx, tx, now
                        break
            except Exception: pass
            return info
            
        try:
            with open('/proc/uptime', 'r') as f:
                sec = float(f.readline().split()[0])
                d, h, m = int(sec // 86400), int((sec % 86400) // 3600), int((sec % 3600) // 60)
                info["uptime"] = f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m"
        except Exception: pass
        
        try:
            with open('/proc/stat', 'r') as f:
                parts = [int(i) for i in f.readline().split()[1:]]
                tot, idle = sum(parts), parts[3] + parts[4]
                if self.last_cpu_total > 0: 
                    info["cpu_usage"] = f"{100.0 * (1.0 - (idle - self.last_cpu_idle) / (tot - self.last_cpu_total)):.1f}%"
                self.last_cpu_total, self.last_cpu_idle = tot, idle
        except Exception: pass
        
        try:
            with open('/proc/meminfo', 'r') as f: mem = f.read()
            mt = int(re.search(r'MemTotal:\s+(\d+)', mem).group(1))
            mf = int(re.search(r'MemFree:\s+(\d+)', mem).group(1))
            mb = int(re.search(r'Buffers:\s+(\d+)', mem).group(1))
            mc = int(re.search(r'Cached:\s+(\d+)', mem).group(1))
            info["ram_usage"] = f"{((mt - mf - mb - mc) / mt) * 100:.1f}%"
        except Exception: pass
        
        try:
            for line in os.popen("sensors 2>/dev/null").read().split('\n'):
                tm = re.search(r'\+?(\d+\.\d+)°?C', line)
                if tm and any(k in line.lower() for k in ['package id 0', 'core 0', 'cputin']):
                    if info["temp_cpu"] == "N/A": info["temp_cpu"] = f"{tm.group(1)}°C"
        except Exception: pass
        
        try:
            now = time.time()
            with open('/proc/net/dev', 'r') as f: lines = f.readlines()[2:]
            rx, tx = 0, 0
            for line in lines:
                if ':' not in line: continue
                iface, data = line.split(':', 1)
                if iface.strip() == 'lo': continue
                parts = data.split()
                rx += int(parts[0]); tx += int(parts[8])
            if self.last_net_time > 0 and (now - self.last_net_time) > 0:
                el = now - self.last_net_time
                if rx >= self.last_rx: info["net_down"] = self.format_speed((rx - self.last_rx) / el)
                if tx >= self.last_tx: info["net_up"] = self.format_speed((tx - self.last_tx) / el)
            self.last_net_time, self.last_rx, self.last_tx = now, rx, tx
        except Exception: pass
        
        return info

    def get_disk_info(self):
        disks = []
        if not self.is_linux: 
            for drive in [f"{d}:" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]:
                try:
                    total, used, free = shutil.disk_usage(f"{drive}\\")
                    percent = (used / total) * 100
                    disks.append({"mount": drive, "size": f"{total//(2**30)}G", "used": f"{used//(2**30)}G", "percent": f"{percent:.1f}"})
                except Exception: pass
            return disks
            
        try: os.system("timeout 2 ls /mnt/NAS/* >/dev/null 2>&1")
        except Exception: pass
        try:
            for line in os.popen("df -hP 2>/dev/null | grep -E '^/dev/|/mnt/NAS'").read().strip().split('\n'):
                if not line: continue
                parts = line.split()
                if len(parts) >= 6 and parts[5] not in ["/home", "/var/log", "/var/cache", "/boot/efi"]:
                    if parts[5] == "/":
                        parts[5] = "File System"
                    disks.append({"mount": os.path.basename(parts[5]) or parts[5], "size": parts[1], "used": parts[2], "percent": parts[4].replace('%', '')})
        except Exception: pass
        return disks

monitor = SystemMonitor()

class StatusChecker:
    PIHOLE_SID = None
    IP_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    @staticmethod
    def is_open(ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                return s.connect_ex((ip, int(port))) == 0
        except Exception:
            return False

    @classmethod
    def check_service(cls, s):
        name = s["name"]
        keys = s.get('_keys', {})
        
        if name in ALWAYS_ONLINE or s.get("type") in ["gateway", "static"]:
            return s["uid"], {"online": True, "extra": ""}
            
        public_url = s.get("public", "").rstrip('/')
        target_ip = ""
        port = s.get("port", 80)
        
        try:
            parsed = urllib.parse.urlparse(public_url)
            if parsed.hostname and cls.IP_REGEX.match(parsed.hostname):
                target_ip = parsed.hostname
                port = parsed.port if parsed.port else (443 if parsed.scheme == 'https' else 80)
            elif parsed.port:
                port = parsed.port
        except Exception:
            pass

        if not target_ip:
            target_ip = s.get("_node_bind_ip", "127.0.0.1")
            
        is_online = cls.is_open(target_ip, port)
        extra = ""
        
        if is_online:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            if name == "Portainer" and keys.get('PORTAINER'):
                try:
                    req = urllib.request.Request(f"{public_url}/api/endpoints", headers={"X-API-Key": keys['PORTAINER']})
                    ep_id = json.loads(urllib.request.urlopen(req, context=ctx, timeout=1.0).read())[0].get("Id", 1)
                    req2 = urllib.request.Request(f"{public_url}/api/endpoints/{ep_id}/docker/containers/json?all=1", headers={"X-API-Key": keys['PORTAINER']})
                    cnts = json.loads(urllib.request.urlopen(req2, context=ctx, timeout=1.0).read())
                    extra = f"{sum(1 for c in cnts if c.get('State') == 'running')}/{SETTINGS['CONTAINERS_NUMBER']} running"
                except Exception: pass
                
            elif name == "Speedtest":
                try:
                    req = urllib.request.Request(f"{public_url}/api/speedtest/latest", headers={"Accept": "application/json"})
                    res = json.loads(urllib.request.urlopen(req, timeout=1.0).read().decode())
                    data = res.get("data", res)
                    extra = f"{float(data.get('ping',0)):.0f} ms &nbsp; \u2193 {float(data.get('download',0)):.0f} Mbps &nbsp; \u2191 {float(data.get('upload',0)):.0f} Mbps"
                except Exception: pass
                
            elif name == "Pi-hole DNS" and keys.get('PIHOLE'):
                try:
                    base_url = public_url.replace('/admin', '').rstrip('/')
                    try:
                        v5_url = f"{base_url}/admin/api.php?summary&auth={keys['PIHOLE'].strip()}"
                        req = urllib.request.Request(v5_url)
                        v5_data = json.loads(urllib.request.urlopen(req, timeout=1.0).read().decode())
                        if 'ads_percentage_today' in v5_data: extra = f"{float(v5_data['ads_percentage_today']):.1f}% Blocked"
                    except Exception: pass
                    
                    if not extra:
                        if not cls.PIHOLE_SID:
                            auth_payload = json.dumps({"password": keys['PIHOLE'].strip()}).encode('utf-8')
                            req_auth = urllib.request.Request(f"{base_url}/api/auth", data=auth_payload, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
                            auth_data = json.loads(urllib.request.urlopen(req_auth, timeout=1.0).read().decode())
                            cls.PIHOLE_SID = auth_data.get("session", {}).get("sid") or auth_data.get("sid")
                        if cls.PIHOLE_SID:
                            req_stats = urllib.request.Request(f"{base_url}/api/stats/summary", headers={'sid': cls.PIHOLE_SID, 'Accept': 'application/json'})
                            try:
                                stats_data = json.loads(urllib.request.urlopen(req_stats, timeout=1.0).read().decode())
                                extra = f"{float(stats_data.get('queries', {}).get('percent_blocked', 0)):.1f}% Blocked"
                            except Exception as e:
                                if hasattr(e, 'code') and e.code == 401: cls.PIHOLE_SID = None
                except Exception: pass

            elif name == "AdGuard Home DNS":
                try:
                    import base64
                    req = urllib.request.Request(f"{public_url}/control/stats")
                    if keys.get('ADGUARD_USER') and keys.get('ADGUARD_PASS'):
                        auth_str = f"{keys['ADGUARD_USER']}:{keys['ADGUARD_PASS']}"
                        b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
                        req.add_header("Authorization", f"Basic {b64}")
                    data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=1.0).read().decode())
                    queries = data.get("num_dns_queries", 0)
                    blocked = data.get("num_blocked_filtering", 0)
                    if queries > 0:
                        extra = f"{(blocked / queries) * 100:.1f}% Blocked"
                except Exception: pass

            elif name == "Jellyfin" and keys.get('JELLYFIN'):
                try:
                    req = urllib.request.Request(f"{public_url}/Sessions")
                    req.add_header("Authorization", f'MediaBrowser Client="Homer", Device="Script", DeviceId="1", Version="1.0", Token="{keys["JELLYFIN"].strip()}"')
                    req.add_header("Accept", "application/json")
                    
                    res = urllib.request.urlopen(req, context=ctx, timeout=3.0)
                    sessions = json.loads(res.read().decode())
                    active_users = [sess.get("UserName", "Unknown") for sess in sessions if sess.get("NowPlayingItem") is not None]
                    extra = f"Watching: {', '.join(set(active_users))}" if active_users else "0 Active Streams"
                except Exception as e:
                    extra = f"API Error: {str(e).replace('<', '[').replace('>', ']')}"

            elif name in ["Seerr", "Seerr Source 1", "Seerr Source 2"]:
                # Pick the correct key depending on which container we are checking
                api_key = keys.get('SEERR_1') if name == "Seerr Source 1" else keys.get('SEERR_2')
                if api_key:
                    try:
                        req = urllib.request.Request(f"{public_url}/api/v1/request/count", headers={"X-Api-Key": api_key})
                        data = json.loads(urllib.request.urlopen(req, timeout=1.0).read().decode())
                        pending = data.get("pending", 0)
                        total = data.get("total", 0)
                        extra = f"{pending} Pending Requests<br>{total} Total Requests"
                    except Exception: pass
                
            elif name == "VueTorrent":
                try:
                    cookie = ""
                    if keys.get('VUETORRENT_USER') and keys.get('VUETORRENT_PASS'):
                        try:
                            auth_data = urllib.parse.urlencode({'username': keys['VUETORRENT_USER'], 'password': keys['VUETORRENT_PASS']}).encode('utf-8')
                            auth_req = urllib.request.Request(f"{public_url}/api/v2/auth/login", data=auth_data)
                            auth_res = urllib.request.urlopen(auth_req, context=ctx, timeout=1.0)
                            cookie = auth_res.getheader('Set-Cookie')
                        except Exception: pass
                    req = urllib.request.Request(f"{public_url}/api/v2/torrents/info")
                    if cookie: req.add_header('Cookie', cookie)
                    torrents = json.loads(urllib.request.urlopen(req, context=ctx, timeout=1.0).read().decode())
                    extra = f"{len(torrents)} Torrents"
                except Exception: pass

            elif name == "VueTorrentRR":
                try:
                    cookie = ""
                    if keys.get('VUETORRENT_USER') and keys.get('VUETORRENT_PASS'):
                        try:
                            auth_data = urllib.parse.urlencode({'username': keys['VUETORRENT_USER'], 'password': keys['VUETORRENT_PASS']}).encode('utf-8')
                            auth_req = urllib.request.Request(f"{public_url}/api/v2/auth/login", data=auth_data)
                            auth_res = urllib.request.urlopen(auth_req, context=ctx, timeout=1.0)
                            cookie = auth_res.getheader('Set-Cookie')
                        except Exception: pass
                    req = urllib.request.Request(f"{public_url}/api/v2/torrents/info")
                    if cookie: req.add_header('Cookie', cookie)
                    torrents = json.loads(urllib.request.urlopen(req, context=ctx, timeout=1.0).read().decode())
                    extra = f"{len(torrents)} Torrents"
                except Exception: pass
                
            elif name == "Navidrome" and keys.get('NAVIDROME_USER') and keys.get('NAVIDROME_PASS'):
                try:
                    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    to_hash = keys['NAVIDROME_PASS'] + salt
                    token = hashlib.md5(to_hash.encode('utf-8')).hexdigest()
                    api_url = f"{public_url}/rest/getNowPlaying?u={keys['NAVIDROME_USER']}&t={token}&s={salt}&v=1.16.1&c=homer_dashboard&f=json"
                    req = urllib.request.Request(api_url)
                    res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=1.0).read().decode())
                    if "subsonic-response" in res and "nowPlaying" in res["subsonic-response"]:
                        now_playing_data = res["subsonic-response"]["nowPlaying"]
                        entries = now_playing_data.get("entry", []) if now_playing_data else []
                        if isinstance(entries, dict): entries = [entries]
                        listeners = sum(1 for sess in entries if int(sess.get("minutesAgo", 0)) < 15)
                        extra = f"{listeners} Listening"
                except Exception: pass

        # Dynamic comments from DASHBOARD_CONFIG
        if is_online and "comment" in s:
            if extra:
                extra += f"<br>{s['comment']}"
            else:
                extra = s["comment"]

        return s["uid"], {"online": is_online, "extra": extra}

class HomerServer(BaseHTTPRequestHandler):
    def end_headers(self):
        origin = self.headers.get('Origin', '')
        if origin: 
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept-Encoding')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def is_auth(self): return 'homer_auth=granted' in self.headers.get('Cookie', '')
    
    def send_compressed_text(self, text, content_type="text/html"):
        try:
            self.send_response(200); self.send_header("Content-type", content_type)
            encoded = text.encode('utf-8')
            if "gzip" in self.headers.get("Accept-Encoding", ""):
                compressed = gzip.compress(encoded)
                self.send_header("Content-Encoding", "gzip"); self.send_header("Content-Length", str(len(compressed))); self.end_headers(); self.wfile.write(compressed)
            else:
                self.send_header("Content-Length", str(len(encoded))); self.end_headers(); self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass # Silently ignore if the browser closed the connection early
        
    def do_POST(self):
        if not self.is_auth(): return self.connection.close()
        try:
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            # Swarm Sync Payload Listener
            if self.path == "/api/homer_sync":
                new_code = data.get("code")
                new_hash = data.get("hash")
                
                # If we receive a new hash, overwrite the file and restart
                if new_hash and new_hash != SCRIPT_HASH:
                    print("Received Swarm Update! Applying and restarting...")
                    with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
                        f.write(new_code)
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "updated"}')
                    threading.Timer(1.0, restart_script).start()
                else:
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "ignored"}')
                return

            # Swarm Certificate Sync Listener (Dynamic target node identification)
            if self.path == "/api/cert_sync":
                fullchain = data.get("fullchain")
                privkey = data.get("privkey")
                
                # Dynamically fetch the local directory for the bound node
                current_node = next((g for g in DASHBOARD_CONFIG if g.get("id") == LOCAL_NODE_ID), {})
                caddy_dir = current_node.get("sync_certs_dir", os.path.join(SETTINGS["DOCKERS_FOLDER"], "caddy", "certs"))
                
                try:
                    os.makedirs(caddy_dir, exist_ok=True)
                    with open(os.path.join(caddy_dir, "fullchain.pem"), "w") as f: f.write(fullchain)
                    with open(os.path.join(caddy_dir, "privkey.pem"), "w") as f: f.write(privkey)
                    
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "certs_saved"}')
                except Exception as e:
                    print(f"CERT SYNC ERROR: {e}")
                    self.send_response(500); self.end_headers()
                return

            if self.path == "/api/reboot":
                if data.get("password") == SETTINGS['REBOOT_PASSWORD']:
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "rebooting"}')
                    os.system(SETTINGS['REBOOT_COMMAND'])
                else: self.send_response(401); self.end_headers()
                return
                
            if self.path == "/api/action":
                uid, action = data.get("uid"), data.get("action")
                
                # SECURITY FIX: Whitelist actions to prevent Remote Code Execution
                if action not in ["start", "stop", "restart", "status"]:
                    self.send_response(400); self.end_headers(); return

                target = ALL_SERVICES.get(uid)
                if target and target.get("_group_controls"):
                    service_id = target.get("service_id", target.get("name")) if target else data.get("service_id")
                    if action == "status":
                        info_text = f""
                        if "script_dir" in target:
                            try:
                                cmd = f"cd '{target['script_dir']}' && bash status.sh"
                                info_text += subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5).decode('utf-8', errors='ignore')
                            except Exception as err:
                                info_text += f"Error reading status script: {err}"
                        else:
                            info_text += f"Local: {target.get('local')}\nPublic: {target.get('public')}"
                        self.send_response(200); self.end_headers()
                        self.wfile.write(json.dumps({"status": "success", "info": info_text}).encode('utf-8'))
                        return
                    if not IS_LINUX:
                        cmd = ""
                        if action == "start": cmd = f"Start-Service -Name '{service_id}'"
                        elif action == "stop": cmd = f"Stop-Service -Name '{service_id}' -Force"
                        elif action == "restart": cmd = f"Restart-Service -Name '{service_id}' -Force"
                        if cmd: subprocess.Popen(["powershell", "-Command", cmd])
                    else:
                        if action == "restart" and "custom_restart" in target: os.system(target['custom_restart'])
                        elif "script_dir" in target: os.system(f"cd '{target['script_dir']}' && bash '{action}.sh' &")
                        elif action in ["start", "stop", "restart"]: subprocess.Popen(["systemctl", action, service_id])
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{"status": "success"}')
                else: self.send_response(400); self.end_headers()
        except Exception: self.send_response(500); self.end_headers()
        
    def do_GET(self):
        if self.path == SETTINGS['SECRET_URL_PATH']:
            self.send_response(302); self.send_header('Set-Cookie', 'homer_auth=granted; Path=/; HttpOnly; SameSite=Lax; Max-Age=3153600000')
            self.send_header('Location', '/'); self.end_headers(); return
            
        if self.path == "/manifest.json":
            self.send_response(200); self.send_header("Content-type", "application/json"); self.send_header("Cache-Control", "public, max-age=31536000"); self.end_headers()
            self.wfile.write(b'{"name":"Homer","short_name":"Homer","start_url":"/","display":"standalone","background_color":"#0f1117","theme_color":"#0f1117","icons":[{"src":"/icon-192.png","sizes":"192x192","type":"image/png"},{"src":"/icon-512.png","sizes":"512x512","type":"image/png"}]}')
            return
            
        for static in [".ico", ".png", ".webmanifest"]:
            if self.path.endswith(static):
                try:
                    with open(os.path.join(os.getcwd(), self.path.lstrip("/")), "rb") as f:
                        self.send_response(200); self.send_header("Content-type", f"image/{'x-icon' if static=='.ico' else 'png'}"); self.send_header("Cache-Control", "public, max-age=31536000"); self.end_headers(); self.wfile.write(f.read())
                except Exception: self.send_response(404); self.end_headers()
                return
                
        if not self.is_auth(): return self.connection.close()

        # Swarm Certificate Pull Endpoint
        if self.path == "/api/cert_pull":
            # Dynamically serve certs from whoever is marked as "is_cert_master"
            master_node = next((g for g in DASHBOARD_CONFIG if g.get("is_cert_master") == True), {})
            master_dir = master_node.get("sync_certs_dir", "")
            
            cert_file = os.path.join(master_dir, "fullchain.pem")
            key_file = os.path.join(master_dir, "privkey.pem")
            
            if os.path.exists(cert_file) and os.path.exists(key_file):
                with open(cert_file, "r") as f: fc = f.read()
                with open(key_file, "r") as f: pk = f.read()
                self.send_response(200); self.send_header("Content-type", "application/json"); self.end_headers()
                self.wfile.write(json.dumps({"fullchain": fc, "privkey": pk}).encode('utf-8'))
            else:
                self.send_response(404); self.end_headers()
            return
        
        # Utility Proxy Endpoint
        if self.path.startswith("/api/proxy?url="):
            self.send_response(200); self.send_header("Content-type", "application/json"); self.end_headers()
            try:
                target_url = urllib.parse.unquote(self.path.split("?url=")[1])
                
                # SECURITY FIX: Prevent Server-Side Request Forgery (SSRF)
                allowed = any(target_url.startswith(s["public"]) for s in ALL_SERVICES.values() if s.get("public"))
                if not allowed:
                    self.wfile.write(b'{"online": false, "error": "unauthorized domain"}')
                    return
                
                req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0 HomerSwarm/1.0'})
                ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                res = urllib.request.urlopen(req, context=ctx, timeout=8.0)
                self.wfile.write(res.read())
            except Exception: self.wfile.write(b'{"online": false, "error": "proxy failed"}')
            return
            
        if self.path.startswith("/api/cert"):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            noproxy = query.get('noproxy', ['0'])[0] == '1'
            cert_data = None
            
            # 1. Try to serve the local certificate if defined and exists
            try:
                if ACTIVE_CERT and os.path.exists(ACTIVE_CERT):
                    with open(ACTIVE_CERT, "rb") as f:
                        cert_data = f.read()
            except Exception: pass
            
            # 2. If no local certificate is found, proxy the request to other backend nodes
            if not cert_data and not noproxy:
                for group in DASHBOARD_CONFIG:
                    if group.get("mode") == "backend" and group.get("api_ip"):
                        target_url = group["api_ip"].replace(SETTINGS['SECRET_URL_PATH'], "/api/cert?noproxy=1")
                        try:
                            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                            req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0 HomerSwarm/1.0', 'Cookie': 'homer_auth=granted'})
                            res = urllib.request.urlopen(req, context=ctx, timeout=3.0)
                            if res.status == 200:
                                cert_data = res.read()
                                break
                        except Exception:
                            continue
                            
            # 3. Return the certificate or 404
            if cert_data:
                self.send_response(200); self.send_header("Content-type", "application/x-pem-file"); self.send_header("Content-Disposition", 'attachment; filename="rootCA.pem"'); self.end_headers(); self.wfile.write(cert_data)
            else:
                self.send_response(404); self.end_headers(); self.wfile.write(b"Certificate not found.")
            return
            
        if self.path.startswith("/api/status"):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            req_node_id = query.get('node', [None])[0]
            status_data = STATUS_CACHE.get(req_node_id, {})
            self.send_compressed_text(json.dumps(status_data), "application/json")
            return
            
        if self.path in ["/api/sysinfo", "/api/disks"]:
            if self.path == "/api/sysinfo": self.send_compressed_text(json.dumps(monitor.get_sys_info()), "application/json")
            elif self.path == "/api/disks": self.send_compressed_text(json.dumps(monitor.get_disk_info()), "application/json")
            return
            
        if self.path in ["/", "/index.html", "/useip"] or self.path.startswith("/?useip"):
            host_header = self.headers.get('Host', '').split(':')[0]
            # Detect if user accessed via IP (defaults to True) or DNS (defaults to False)
            is_pub = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host_header) is not None
            self.send_compressed_text(self.generate_html(default_public=is_pub), "text/html")
            return
            
        self.send_response(404); self.end_headers()

    def generate_html(self, default_public=False):
        js_config = []
        tab_buttons = ""
        html_panes = ""
        
        for i, group in enumerate(DASHBOARD_CONFIG):
            g_id = group.get("id", f"tab_{i}")
            active_class = "active" if i == 0 else ""
            display_style = "display: block;" if i == 0 else "display: none;"
            
            js_config.append({
                "id": g_id,
                "api_ip": group.get("api_ip", ""),
                "api_dns": group.get("api_dns", ""),
                "domain_names": group.get("domain_names", []),
                "color": group["color"],
                "mode": group.get("mode")
            })
            
            tab_buttons += f'<button class="tab-btn {active_class}" id="tab-btn-{g_id}" style="--theme-color: {group["color"]};" onclick="openTab(\'{g_id}\')">{group["title"]}</button>'
            
            html_panes += f'<div id="pane-{g_id}" class="tab-pane" style="{display_style}">'
            
            if group.get("mode") != "static":
                html_panes += f'''<div class="server-header"><h1 class="section-title" style="margin-top:0; border:none;">Services</h1><button class="server-reboot-btn" onclick="reqServerReboot('{g_id}', '{group["title"]}')">Reboot Server</button></div>'''
            else:
                html_panes += f'''<div class="server-header"><h1 class="section-title" style="margin-top:0; border:none;">Static Cloud Backup Services</h1></div>'''
                
            html_panes += '<div class="grid">'
            for s in group["items"]:
                url = s.get("url", s.get("public") if default_public else s.get("local"))
                d_loc = s.get("local", s.get("url"))
                d_pub = s.get("public", s.get("url"))
                controls = "true" if group.get("allow_controls") else "false"
                dots_html = f'''<div class="kebab-menu" onclick="event.preventDefault(); event.stopPropagation(); showMenu('{s["uid"]}');">&#8942;</div>''' if controls == "true" else ""
                is_gateway = s["name"] in ["Cloud Gateway", "Jellyfin Gateway", "Navidrome Gateway"]
                onclick_logic = f"event.preventDefault(); openGatewayModal('{s['name']}');" if is_gateway else "selCard(this.querySelector('.card'))"
                
                html_panes += f'''<a href="{url}" target="_blank" rel="noopener noreferrer" class="card-link" data-local="{d_loc}" data-public="{d_pub}" data-uid="{s["uid"]}" data-name="{s["name"]}" onclick="{onclick_logic}"><div class="card" id="card-{s["uid"]}" style="--theme-color: {group["color"]};">{dots_html}<h2>{s["name"]}</h2><p id="status-{s["uid"]}" style="font-weight:bold;">Checking...</p></div></a>'''
            
            html_panes += '</div><hr class="horizontal-divider" style="margin-top:0; border:none;">'
            html_panes += f'<h1 class="section-title" style="margin-top:0;">Storage</h1><div class="disk-grid" id="disks-{g_id}"><span style="color:#6c757d;font-size:14px;">Loading drives...</span></div></div>'
        
        return f"""<!DOCTYPE html>
<html lang="en" style="background-color: #0f1117;">
<head>
    <meta charset="UTF-8">
    <title>Homer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0f1117">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Homer">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        body {{background:#0f1117;color:#fff;font-family:sans-serif;padding:20px;margin:0;padding-bottom:120px;}}
        .top-bar {{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}}
        h1 {{margin:0;font-size:24px;}}
        .cert-btn {{ background: #1c1f26; color: #8e95a0; font-weight: bold; border: 1px solid #2b2f36; padding: 6px 12px; border-radius: 6px; cursor: pointer; transition: 0.2s; font-size: 13px; }}
        .cert-btn:hover {{ background: #2b2f36; color: #fff; border-color: #00ff99; }}
        .switch-container {{display:flex;align-items:center;gap:10px;cursor:pointer;height:32px;}}
        .switch {{width:50px;height:26px;background:#2b2f36;border-radius:20px;position:relative;}}
        .switch.active {{background:#00ff99;box-shadow:0 0 10px #00ff99;}}
        .slider {{width:22px;height:22px;background:#fff;border-radius:50%;position:absolute;top:2px;left:2px;transition:.2s;}}
        .switch.active .slider {{transform:translateX(24px);}}
        .tab-container {{ display: flex; gap: 15px; margin-bottom: 25px; border-bottom: 2px solid #2b2f36; padding-bottom: 15px; overflow-x: auto; }}
        .tab-container::-webkit-scrollbar {{ display: none; }}
        .tab-btn {{ background: #1c1f26; color: #8e95a0; border: 2px solid transparent; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 15px; transition: 0.2s; white-space: nowrap; }}
        .tab-btn:hover {{ background: #2b2f36; color: #fff; }}
        .tab-btn.active {{ color: #fff; border-color: var(--theme-color); background: #111a22; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
        .server-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .server-reboot-btn {{ background: #ff4444; color: #fff; box-shadow: 0 0 12px rgba(255, 68, 68, 0.4); border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 13px; }}
        .server-reboot-btn:active {{ transform: scale(0.95); }}
        .grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;}}
        .card-link {{text-decoration:none;color:inherit;display:block;-webkit-touch-callout:none;user-select:none;}}
        .card {{background:#1c1f26;padding:20px;border-radius:10px;cursor:pointer;border:2px solid transparent;transition:.2s;height:100%;box-sizing:border-box;position:relative;}}
        .card:hover {{border-color: var(--theme-color);}} 
        .card.active {{border-color: var(--theme-color); background:#111a22; box-shadow:0 0 15px var(--theme-color);}}
        .kebab-menu {{position:absolute;top:10px;right:10px;font-size:24px;line-height:16px;color:#8e95a0;cursor:pointer;padding:8px;border-radius:6px;transition:.2s;z-index:10;}}
        .kebab-menu:hover {{color:#fff;background:rgba(255,255,255,0.1);}}
        .section-title {{margin-top:20px;font-size:18px;color:#eaeaea;border-bottom:1px solid #2b2f36;padding-bottom:10px;}}
        .disk-grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-top:15px;}}
        .disk-card {{background:#1c1f26;padding:15px;border-radius:8px;border:1px solid #2b2f36;}}
        .disk-header {{display:flex;justify-content:space-between;font-size:13px;margin-bottom:10px;}}
        .progress-bar-bg {{background:#0f1117;border-radius:4px;height:8px;width:100%;overflow:hidden;}}
        .progress-bar-fill {{background:#00ff99;height:100%;transition:width 0.5s ease;}}
        .progress-bar-fill.warning {{background:#ffaa00;}} .progress-bar-fill.danger {{background:#ff4444;}}
        #menu-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.45); z-index: 9998; opacity: 0; visibility: hidden; transition: opacity 0.3s ease; backdrop-filter: blur(3px); -webkit-backdrop-filter: blur(3px); }}
        #menu-overlay.active {{ opacity: 1; visibility: visible; }}
        #action-sheet-container {{ position: fixed; bottom: -100%; left: 50%; transform: translateX(-50%); width: 95%; max-width: 400px; z-index: 9999; transition: bottom 0.3s cubic-bezier(0.2, 0.8, 0.2, 1); display: flex; flex-direction: column; gap: 8px; padding-bottom: max(15px, env(safe-area-inset-bottom)); }}
        #action-sheet-container.active {{ bottom: 0; }}
        .action-group {{ background: rgba(35, 38, 45, 0.85); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; }}
        .action-group .menu-title {{ text-align: center; padding: 14px; font-size: 13px; color: #8e95a0; border-bottom: 1px solid rgba(255,255,255,0.1); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
        .action-group button {{ width: 100%; background: transparent; color: #fff; border: none; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 18px 20px; text-align: center; font-size: 18px; cursor: pointer; transition: background 0.2s; margin: 0; }}
        .action-group button:last-child {{ border-bottom: none; }}
        .action-group button:active {{ background: rgba(255,255,255,0.15); }}
        .cancel-group button {{ font-weight: 600; color: #ff4444; }}
        .sysinfo-bar {{position:fixed;bottom:0;left:0;width:100%;background:rgba(28, 31, 38, 0.95);backdrop-filter:blur(5px);border-top:1px solid #2b2f36;z-index:1000;overflow-x:auto;-webkit-overflow-scrolling:touch;display:flex;justify-content:center;}}
        .sysinfo-bar::-webkit-scrollbar {{display:none;}}
        .sysinfo-inner {{display:flex;justify-content:space-evenly;align-items:center;width:100%;max-width:1200px;min-width:650px;padding:12px 15px;box-sizing:border-box;}}
        .sysinfo-item {{ display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }}
        .sysinfo-label {{ color: #6c757d; font-size: 10px; text-transform: uppercase; margin-bottom: 4px; }}
        .sysinfo-value {{ color: #00ff99; font-weight: bold; font-size: 15px; font-family: monospace; }}
        .horizontal-divider {{border:none;border-bottom:1px solid #2b2f36;margin:40px 0;}}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .tab-pane {{ animation: fadeIn 0.3s ease; }}
        #gateway-modal-container {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0.95); background: rgba(35, 38, 45, 0.95); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid #2b2f36; border-radius: 14px; padding: 20px; width: 90%; max-width: 400px; z-index: 10000; opacity: 0; visibility: hidden; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        #gateway-modal-container.active {{ opacity: 1; visibility: visible; transform: translate(-50%, -50%) scale(1); }}
        .gateway-title {{ text-align: center; color: #fff; font-size: 18px; font-weight: bold; margin-bottom: 5px; }}
        .gateway-btn {{ background: #1c1f26; color: #00ff99; border: 1px solid #2b2f36; padding: 12px 15px; border-radius: 8px; cursor: pointer; text-align: left; font-size: 15px; transition: 0.2s; display: flex; flex-direction: column; text-decoration: none; }}
        .gateway-btn:hover {{ background: #2b2f36; border-color: #00ff99; }}
        .gateway-btn-title {{ font-weight: bold; color: #fff; margin-bottom: 4px; }}
        .gateway-btn-url {{ font-size: 12px; color: #8e95a0; word-break: break-all; }}
        .gateway-cancel {{ background: transparent; color: #ff4444; border: none; padding: 12px; text-align: center; cursor: pointer; font-weight: bold; margin-top: 5px; border-radius: 8px; }}
        .gateway-cancel:hover {{ background: rgba(255, 68, 68, 0.1); }}
        #status-modal-container {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0.95); background: rgba(35, 38, 45, 0.95); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid #2b2f36; border-radius: 14px; padding: 20px; width: 90%; max-width: 450px; z-index: 10000; opacity: 0; visibility: hidden; transition: all 0.2s ease; display: flex; flex-direction: column; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        #status-modal-container.active {{ opacity: 1; visibility: visible; transform: translate(-50%, -50%) scale(1); }}
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Our Network Solutions Gateway</h1>
        <div style="display: flex; align-items: center; gap: 15px;">
            <button class="cert-btn" title="Download CA Certificate" onclick="downloadCert()">CA</button>
            <div class="switch-container" onclick="togMode()">
                <span id="mode-label">{"IP" if default_public else "DNS"}</span>
                <div class="switch {'active' if default_public else ''}" id="mode-switch"><div class="slider"></div></div>
            </div>
        </div>
    </div>
    
    <div class="tab-container">{tab_buttons}</div>
    {html_panes}
    
    <div class="sysinfo-bar">
        <div class="sysinfo-inner">
            <div class="sysinfo-item"><span class="sysinfo-label">Uptime</span><span class="sysinfo-value" id="sys-uptime">N/A</span></div>
            <div class="sysinfo-item"><span class="sysinfo-label">DL Speed</span><span class="sysinfo-value" id="sys-net-down">N/A</span></div>
            <div class="sysinfo-item"><span class="sysinfo-label">UL Speed</span><span class="sysinfo-value" id="sys-net-up">N/A</span></div>
            <div class="sysinfo-item"><span class="sysinfo-label">CPU Use</span><span class="sysinfo-value" id="sys-cpu-use">N/A</span></div>
            <div class="sysinfo-item"><span class="sysinfo-label">RAM Use</span><span class="sysinfo-value" id="sys-ram-use">N/A</span></div>
            <div class="sysinfo-item"><span class="sysinfo-label">CPU Temp</span><span class="sysinfo-value" id="sys-cpu-temp">N/A</span></div>
        </div>
    </div>
    
    <div id="menu-overlay" onclick="closeMenu(); closeGatewayModal(); closeStatusModal();"></div>

    <div id="action-sheet-container">
        <div class="action-group">
            <div class="menu-title">Service Actions</div>
            <button onclick="sendAct('start')">Start</button>
            <button onclick="sendAct('stop')">Stop</button>
            <button onclick="sendAct('restart')">Restart</button>
            <button id="action-btn-status" style="display:none;" onclick="sendAct('status')">Status</button>
        </div>
        <div class="action-group cancel-group"><button onclick="closeMenu()">Cancel</button></div>
    </div>
    
    <div id="gateway-modal-container">
        <div class="gateway-title" id="gateway-modal-title">Select Link</div>
        <div id="gateway-modal-list" style="display:flex; flex-direction:column; gap:8px;"></div>
        <button class="gateway-cancel" onclick="closeGatewayModal()">Cancel</button>
    </div>

    <div id="status-modal-container">
        <div class="gateway-title" id="status-modal-title">Server Information</div>
        <pre id="status-modal-text" style="background:#1c1f26; color:#00ff99; padding:12px; border-radius:8px; white-space:pre-wrap; max-height:220px; overflow-y:auto; font-size:13px; font-family:monospace; margin:10px 0; border:1px solid #2b2f36;"></pre>
        <button class="gateway-cancel" style="width:100%; margin:0;" onclick="closeStatusModal()">Close</button>
    </div>
    
    <script>
        const gatewayData = {json.dumps(GATEWAY_CONFIG)};
        
        function downloadCert() {{
              alert(
                "Downloading Certificate (rootCA.pem)...\\n\\n" +
                "INSTALLATION GUIDE:\\n" +
                "• iOS: Open downloaded file -> Install Profile -> Go to Settings > General > About > Certificate Trust Settings -> Enable Full Trust.\\n" +
                "• Windows: Open certmgr > Trusted Root Certification > Certificates > Import certificate file.\\n" +
                "• Mac: Double-click file -> Keychain Access -> Find 'mkcert' -> Get Info -> Trust -> Always Trust.\\n" +
                "• Android: Settings > Security > Encryption & Credentials > Install a certificate > CA certificate."
            );
            window.location.href = '/api/cert'; 
        }}
        
        function openGatewayModal(serviceName) {{
            const data = gatewayData[serviceName];
            if (!data) return;
            document.getElementById('gateway-modal-title').innerText = serviceName;
            const list = document.getElementById('gateway-modal-list'); list.innerHTML = "";
            data.forEach(item => {{
                let a = document.createElement('a'); a.className = "gateway-btn"; a.href = item.url; a.target = "_blank";
                a.innerHTML = `<span class="gateway-btn-title">${{item.title}}</span><span class="gateway-btn-url">${{item.url}}</span>`;
                a.onclick = function() {{ closeGatewayModal(); }}; list.appendChild(a);
            }});
            document.getElementById('menu-overlay').classList.add('active');
            document.getElementById('gateway-modal-container').classList.add('active');
        }}
        
        function closeGatewayModal() {{
            let modal = document.getElementById('gateway-modal-container'); if (modal) modal.classList.remove('active');
            if (!document.getElementById('action-sheet-container').classList.contains('active') && !document.getElementById('status-modal-container').classList.contains('active')) document.getElementById('menu-overlay').classList.remove('active');
        }}
        
        function closeStatusModal() {{
            let modal = document.getElementById('status-modal-container'); if (modal) modal.classList.remove('active');
            if (!document.getElementById('action-sheet-container').classList.contains('active') && !document.getElementById('gateway-modal-container').classList.contains('active')) document.getElementById('menu-overlay').classList.remove('active');
        }}
        
        // Persistent IP Mode Logic
        let savedMode = localStorage.getItem('homer_use_ip');
        let useIp = savedMode !== null ? (savedMode === 'true') : {"true" if default_public else "false"};
        
        const serverGroups = {json.dumps(js_config)};
        let currentTabId = null; let activeUid = null;
        const sheet = document.getElementById('action-sheet-container'); const overlay = document.getElementById('menu-overlay');
        let isVisible = true;
        
        document.addEventListener("visibilitychange", () => {{
            isVisible = document.visibilityState === "visible";
            if (isVisible && currentTabId) {{ updStat(); updSys(); updDisk(); }}
        }});
        
        function initTabs() {{
            let host = window.location.hostname;
            let matched = serverGroups.find(g => g.domain_names && g.domain_names.includes(host));
            if (!matched && (host === 'localhost' || host === '127.0.0.1')) matched = serverGroups.find(g => g.id === 'main');
            let startId = matched ? matched.id : serverGroups[0].id;
            
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('pane-' + startId).style.display = 'block';
            document.getElementById('tab-btn-' + startId).classList.add('active');
            currentTabId = startId;
            
            let modeSwitch = document.getElementById("mode-switch");
            let modeLabel = document.getElementById("mode-label");
            if (useIp) {{
                modeSwitch.classList.add("active");
                modeLabel.innerText = "IP";
            }} else {{
                modeSwitch.classList.remove("active");
                modeLabel.innerText = "DNS";
            }}
            document.querySelectorAll('.card-link').forEach(l => l.href = useIp ? l.getAttribute('data-public') : l.getAttribute('data-local'));

            updSys(); updDisk(); updStat();
        }}
        
        function openTab(id) {{
            let node = serverGroups.find(g => g.id === id);
            let host = window.location.hostname;
            let isCurrentNode = node.domain_names && node.domain_names.includes(host);
            
            if (!isCurrentNode && (host === 'localhost' || host === '127.0.0.1') && id === 'main') {{
                isCurrentNode = true;
            }}
            
            if (!isCurrentNode && node) {{
                let targetUrl = useIp ? node.api_ip : node.api_dns;
                if (targetUrl) {{
                    window.location.href = targetUrl;
                    return;
                }}
            }}
            
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('pane-' + id).style.display = 'block';
            document.getElementById('tab-btn-' + id).classList.add('active');
            currentTabId = id;
            
            updSys(); updDisk(); updStat();
        }}
        
        function togMode() {{
            useIp = !useIp; 
            localStorage.setItem('homer_use_ip', useIp);
            document.getElementById("mode-switch").classList.toggle("active");
            document.getElementById("mode-label").innerText = useIp ? "IP" : "DNS";
            document.querySelectorAll('.card-link').forEach(l => l.href = useIp ? l.getAttribute('data-public') : l.getAttribute('data-local'));
            updStat();
        }}
        
        function selCard(el) {{ document.querySelectorAll('.card').forEach(c => c.classList.remove('active')); if (el) el.classList.add('active'); }}
        function showMenu(uid) {{ 
            activeUid = uid; 
            let linkEl = document.querySelector('a.card-link[data-uid="' + uid + '"]');
            let sName = linkEl ? linkEl.getAttribute('data-name') : '';
            let statusBtn = document.getElementById('action-btn-status');
            if (statusBtn) {{
                statusBtn.style.display = (sName === 'Project Zomboid') ? 'block' : 'none';
            }}
            overlay.classList.add('active'); 
            sheet.classList.add('active'); 
        }}
        function closeMenu() {{ overlay.classList.remove('active'); sheet.classList.remove('active'); }}
        
        async function sendAct(act) {{
            if (!activeUid) return;
            let safeUid = activeUid; closeMenu();
            try {{
                let payload = JSON.stringify({{ uid: safeUid, action: act }});
                let req = await fetch('/api/action', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: payload }});
                if (req.ok) {{
                    let resData = await req.json();
                    if (act === 'status') {{
                        document.getElementById('status-modal-text').innerText = resData.info || "No status information available.";
                        document.getElementById('menu-overlay').classList.add('active');
                        document.getElementById('status-modal-container').classList.add('active');
                    }} else {{
                        alert(act.toUpperCase() + " command sent!"); 
                        updStat();
                    }}
                }} else {{ alert('Failed.'); }}
            }} catch (e) {{ alert('Error communicating with backend.'); }}
        }}
        
        async function reqServerReboot(id, name) {{
            let pw = prompt(`Enter password to reboot ${{name}}:`); if (!pw) return;
            try {{
                let r = await fetch('/api/reboot', {{ method: 'POST', body: JSON.stringify({{ password: pw }}) }}); 
                if(r.ok) alert(`${{name}} is Rebooting...`); else alert("Wrong password or request failed."); 
            }} catch (e) {{ alert("Remote agent unreachable."); }}
        }}
        
        async function fetchNodeData(path) {{
            try {{
                let controller = new AbortController(); 
                let timeoutId = setTimeout(() => controller.abort(), 4000);
                let r = await fetch(path, {{ signal: controller.signal }});
                clearTimeout(timeoutId);
                return r;
            }} catch(e) {{
                return null;
            }}
        }}
        
        async function updStat() {{
            if (!isVisible || !currentTabId) return;
            let node = serverGroups.find(n => n.id === currentTabId);
            
            if (node && node.mode === 'static') {{
                document.querySelectorAll(`#pane-${{currentTabId}} .card-link`).forEach(el => {{
                    let statEl = el.querySelector('p[id^="status-"]');
                    if (statEl) {{ statEl.innerHTML = "Online"; statEl.style.color = "#00ff99"; }}
                }});
                return;
            }}
            
            try {{
                let res = await fetchNodeData('/api/status?node=' + node.id);
                if (res && res.ok) {{
                    let d = await res.json();
                    for (let [uid, info] of Object.entries(d)) {{
                        let el = document.getElementById('status-' + uid);
                        if (el) {{
                            let html = info.online ? "Online" : "Offline";
                            if (info.extra) html += `<br><span style="font-size:13px;color:#8e95a0;font-weight:600;">${{info.extra}}</span>`;
                            if (el.innerHTML !== html) el.innerHTML = html; 
                            el.style.color = info.online ? "#00ff99" : "#ff4444";
                        }}
                    }}
                }}
            }} catch (e) {{
                // Fallback ignore: avoid wiping the status boards if request gets temporarily blocked
            }}
        }}
        
        async function updDisk() {{
            if (!isVisible || !currentTabId) return; 
            let node = serverGroups.find(n => n.id === currentTabId);
            let c = document.getElementById('disks-' + currentTabId); if (!c) return;
            
            if (node && node.mode === 'static') {{
                c.innerHTML = '<span style="color:#6c757d;font-size:14px;">Storage not available on GitHub backup.</span>'; return;
            }}
            try {{
                let res = await fetchNodeData('/api/disks');
                if (!res || !res.ok) throw new Error("Storage Offline");
                let d = await res.json();
                if (!d.length) {{ c.innerHTML = '<span style="color:#6c757d;font-size:14px;">No drives found.</span>'; return; }}
                let h = d.map(x => `<div class="disk-card"><div class="disk-header"><span style="font-weight:bold;color:#fff;">${{x.mount}}</span><span style="color:#8e95a0;">${{x.used}} / ${{x.size}} (${{x.percent}}%)</span></div><div class="progress-bar-bg"><div class="progress-bar-fill ${{x.percent>90?'danger':x.percent>75?'warning':''}}" style="width:${{x.percent}}%"></div></div></div>`).join('');
                if (c.innerHTML !== h) c.innerHTML = h;
            }} catch (e) {{ c.innerHTML = '<span style="color:#ff4444;">Storage monitoring unreachable.</span>'; }}
        }}
        
        async function updSys() {{
            if (!isVisible || !currentTabId) return; 
            let node = serverGroups.find(n => n.id === currentTabId);
            const map = {{ 'uptime': 'sys-uptime', 'net_down': 'sys-net-down', 'net_up': 'sys-net-up', 'cpu_usage': 'sys-cpu-use', 'ram_usage': 'sys-ram-use', 'temp_cpu': 'sys-cpu-temp' }};
            
            if (node && node.mode === 'static') {{ for (let k in map) document.getElementById(map[k]).innerText = 'N/A'; return; }}
            
            try {{
                let res = await fetchNodeData('/api/sysinfo');
                if (!res || !res.ok) throw new Error("Offline");
                let d = await res.json();
                for (let key in map) {{
                    let el = document.getElementById(map[key]);
                    if (el && d[key] !== undefined && el.innerText !== d[key]) el.innerText = d[key];
                }}
            }} catch (e) {{
                for (let key in map) {{ let el = document.getElementById(map[key]); if (el) el.innerText = 'N/A'; }}
            }}
        }}
        
        // --- SPATIAL & ALPHABETICAL NAVIGATION ---
        document.addEventListener('keydown', e => {{
            if (e.key === 'Enter') {{
                let a = document.querySelector('.card.active');
                if (a) a.closest('.card-link').click();
                return;
            }}
            
            let activePane = document.querySelector('.tab-pane[style*="display: block"]');
            if (!activePane) return;
            let cards = Array.from(activePane.querySelectorAll('.card-link'));
            if (!cards.length) return;
            
            if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) {{
                e.preventDefault();
                let cardDivs = cards.map(c => c.querySelector('.card'));
                let currentIdx = cardDivs.findIndex(c => c.classList.contains('active'));
                
                if (currentIdx === -1) {{
                    selCard(cardDivs[0]);
                    cardDivs[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    return;
                }}
                
                let currentRect = cardDivs[currentIdx].getBoundingClientRect();
                let nextIdx = currentIdx;
                
                if (e.key === 'ArrowRight') {{
                    if (currentIdx < cardDivs.length - 1) nextIdx = currentIdx + 1;
                }} else if (e.key === 'ArrowLeft') {{
                    if (currentIdx > 0) nextIdx = currentIdx - 1;
                }} else if (e.key === 'ArrowDown') {{
                    let targets = cardDivs.slice(currentIdx + 1).filter(c => c.getBoundingClientRect().top >= currentRect.bottom - 10);
                    if (targets.length) {{
                        targets.sort((a, b) => Math.abs(a.getBoundingClientRect().left - currentRect.left) - Math.abs(b.getBoundingClientRect().left - currentRect.left));
                        nextIdx = cardDivs.indexOf(targets[0]);
                    }} else {{
                        nextIdx = cardDivs.length - 1; 
                    }}
                }} else if (e.key === 'ArrowUp') {{
                    let targets = cardDivs.slice(0, currentIdx).filter(c => c.getBoundingClientRect().bottom <= currentRect.top + 10);
                    if (targets.length) {{
                        targets.sort((a, b) => Math.abs(a.getBoundingClientRect().left - currentRect.left) - Math.abs(b.getBoundingClientRect().left - currentRect.left));
                        nextIdx = cardDivs.indexOf(targets[0]);
                    }} else {{
                        nextIdx = 0; 
                    }}
                }}
                
                if (nextIdx !== currentIdx) {{
                    selCard(cardDivs[nextIdx]);
                    cardDivs[nextIdx].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                }}
                return;
            }}
            
            if (!e.ctrlKey && !e.altKey && !e.metaKey && e.key.length === 1) {{
                let char = e.key.toLowerCase();
                let matches = cards.filter(link => {{
                    let name = link.getAttribute('data-name');
                    return name && name.toLowerCase().startsWith(char);
                }});
                if (matches.length > 0) {{
                    let currentActive = document.querySelector('.card.active');
                    let nextMatch = matches[0];
                    if (currentActive) {{
                        let idx = matches.indexOf(currentActive.closest('.card-link'));
                        if (idx !== -1 && idx + 1 < matches.length) nextMatch = matches[idx + 1];
                    }}
                    let card = nextMatch.querySelector('.card');
                    selCard(card);
                    card.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                }}
            }}
        }});
        
        setTimeout(() => {{ 
            initTabs();
            setInterval(updStat, 10000);   // Was 5000 (10 seconds is better)
            setInterval(updSys, 10000);    // Was 3000 (10 seconds is better)
            setInterval(updDisk, 300000);  // Was 60000 (disks don't change often, 5 minutes)
        }}, 100);
    </script>
</body>
</html>"""

def watch_file_changes():
    global SCRIPT_HASH
    last_mtime = os.path.getmtime(SCRIPT_PATH)
    while True:
        time.sleep(3)
        try:
            current_mtime = os.path.getmtime(SCRIPT_PATH)
            if current_mtime > last_mtime:
                last_mtime = current_mtime
                time.sleep(0.5) 
                
                with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
                    new_code = f.read()
                
                try:
                    ast.parse(new_code)
                except SyntaxError as e:
                    print(f"Syntax error detected in save, aborting swarm sync: {e}")
                    continue
                    
                new_hash = hashlib.md5(new_code.encode('utf-8')).hexdigest()
                if new_hash != SCRIPT_HASH:
                    print("Local code change detected! Pushing to Swarm Nodes...")
                    SCRIPT_HASH = new_hash
                    payload = json.dumps({"hash": new_hash, "code": new_code}).encode('utf-8')
                    
                    for group in DASHBOARD_CONFIG:
                        # Dynamic push: Send to all backend nodes EXCEPT the current node
                        if group.get("mode") == "backend" and group.get("api_ip") and group.get("id") != LOCAL_NODE_ID:
                            target_url = group["api_ip"].replace(SETTINGS['SECRET_URL_PATH'], "/api/homer_sync")
                            try:
                                req = urllib.request.Request(target_url, data=payload, headers={'Content-Type': 'application/json', 'Cookie': 'homer_auth=granted'})
                                ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                                urllib.request.urlopen(req, context=ctx, timeout=3.0)
                                print(f"Successfully pushed to {group['title']}")
                            except Exception:
                                pass
                    
                    threading.Timer(1.0, restart_script).start()
        except Exception:
            pass

STATUS_CACHE = {}

def background_status_updater():
    """Continuously caches service status in the background for instant web loading."""
    while True:
        try:
            for node_id in set(s["_node_id"] for s in ALL_SERVICES.values()):
                target_svcs = [s for s in ALL_SERVICES.values() if s["_node_id"] == node_id]
                node_status = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(target_svcs))) as ex:
                    for uid, status in ex.map(StatusChecker.check_service, target_svcs):
                        node_status[uid] = status
                STATUS_CACHE[node_id] = node_status
        except Exception:
            pass
        time.sleep(5) # Refresh the cache every 5 seconds

def cert_swarm_loop():
    """Handles dynamically pushing certs from the master and pulling certs to any backend nodes."""
    
    # 1. Dynamically identify the master node from the config
    master_node = next((g for g in DASHBOARD_CONFIG if g.get("is_cert_master") == True), {})
    current_node = next((g for g in DASHBOARD_CONFIG if g.get("id") == LOCAL_NODE_ID), {})
    
    master_id = master_node.get("id")
    
    # If no master is defined, exit the swarm loop to prevent errors
    if not master_id:
        return

    master_certs_dir = master_node.get("sync_certs_dir", "")
    local_certs_dir = current_node.get("sync_certs_dir", os.path.join(SETTINGS["DOCKERS_FOLDER"], "caddy", "certs"))
    
    master_cert = os.path.join(master_certs_dir, "fullchain.pem")
    master_key = os.path.join(master_certs_dir, "privkey.pem")
    
    local_cert = os.path.join(local_certs_dir, "fullchain.pem")
    local_key = os.path.join(local_certs_dir, "privkey.pem")
    
    last_mtime = 0
    
    while True:
        time.sleep(15) 
        try:
            # ==========================================
            # MASTER NODE LOGIC (PUSH)
            # ==========================================
            if LOCAL_NODE_ID == master_id and os.path.exists(master_certs_dir):
                if os.path.exists(master_cert) and os.path.exists(master_key):
                    current_mtime = os.path.getmtime(master_cert)
                    if last_mtime == 0:
                        last_mtime = current_mtime
                    elif current_mtime > last_mtime:
                        last_mtime = current_mtime
                        print(f"CERT SWARM: Detected certificate update on {master_node['title']}. Pushing to external nodes...")
                        
                        with open(master_cert, "r") as f: fc = f.read()
                        with open(master_key, "r") as f: pk = f.read()
                        payload = json.dumps({"fullchain": fc, "privkey": pk}).encode('utf-8')
                        
                        for group in DASHBOARD_CONFIG:
                            # Push to all backend peers EXCEPT the master node
                            if group.get("mode") == "backend" and group.get("id") != master_id and group.get("api_ip"):
                                target_url = group["api_ip"].replace(SETTINGS['SECRET_URL_PATH'], "/api/cert_sync")
                                try:
                                    req = urllib.request.Request(target_url, data=payload, headers={'Content-Type': 'application/json', 'Cookie': 'homer_auth=granted'})
                                    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                                    urllib.request.urlopen(req, context=ctx, timeout=8.0)
                                    print(f"CERT SWARM: Successfully pushed to {group['title']}.")
                                except Exception as e:
                                    print(f"CERT SWARM ERROR: Failed to push to {group['title']}: {e}")

            # ==========================================
            # SECONDARY NODE LOGIC (PULL)
            # ==========================================
            elif LOCAL_NODE_ID != master_id:
                if not os.path.exists(local_cert) or not os.path.exists(local_key):
                    print(f"CERT SWARM: Local certificates missing! Requesting from {master_node['title']}...")
                    
                    if master_node.get("api_ip"):
                        target_url = master_node["api_ip"].replace(SETTINGS['SECRET_URL_PATH'], "/api/cert_pull")
                        try:
                            req = urllib.request.Request(target_url, headers={'Cookie': 'homer_auth=granted'})
                            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                            res = urllib.request.urlopen(req, context=ctx, timeout=8.0)
                            
                            if res.status == 200:
                                data = json.loads(res.read().decode())
                                os.makedirs(local_certs_dir, exist_ok=True)
                                with open(local_cert, "w") as f: f.write(data["fullchain"])
                                with open(local_key, "w") as f: f.write(data["privkey"])
                                print(f"CERT SWARM: Successfully pulled and saved certificates from {master_node['title']}.")
                        except Exception as e:
                            print(f"CERT SWARM ERROR: Failed to pull from {master_node['title']}: {e}")
        except Exception:
            pass

def auto_throttle_loop():
    """Background automation to throttle qBittorrent when Jellyfin is playing, respecting schedules."""
    was_watching_global = None

    print("AUTOMATION: Background loop started. Checking servers for cross-node throttling...")

    while True:
        time.sleep(10) 
        
        is_watching_global = False
        
        for node in DASHBOARD_CONFIG:
            if not node.get("enable_auto_throttle"):
                continue
                
            jellyfin_key = node.get("keys", {}).get("JELLYFIN")
            jellyfin_svc = next((i for i in node.get("items", []) if i["name"] == "Jellyfin"), None)
            
            if jellyfin_key and jellyfin_svc:
                jellyfin_url = jellyfin_svc.get("public", "").rstrip('/')
                try:
                    req = urllib.request.Request(f"{jellyfin_url}/Sessions?api_key={jellyfin_key}")
                    req.add_header("User-Agent", "HomerAutomation/1.0")
                    
                    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                    
                    response = urllib.request.urlopen(req, context=ctx, timeout=3.0)
                    sessions = json.loads(response.read().decode())
                    
                    if any(sess.get('NowPlayingItem') is not None for sess in sessions):
                        is_watching_global = True
                except Exception as e:
                    pass

        if is_watching_global != was_watching_global:
            for node in DASHBOARD_CONFIG:
                has_seerr = any(i["name"] in ("Seerr", "Seerr Source 1", "Seerr Source 2") for i in node.get("items", []))
                has_qbit = any(i["name"] in ("VueTorrent", "VueTorrentRR") for i in node.get("items", []))
                
                if node.get("enable_auto_throttle") or (has_seerr and has_qbit):
                    qbit_svc = next((i for i in node.get("items", []) if i["name"] in ("VueTorrent", "VueTorrentRR")), None)
                    
                    if not qbit_svc:
                        continue
                        
                    qbit_url = qbit_svc.get("public", "").rstrip('/')
                    qbit_user = node.get("keys", {}).get("VUETORRENT_USER")
                    qbit_pass = node.get("keys", {}).get("VUETORRENT_PASS")
                    
                    try:
                        cookie = ""
                        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                        
                        if qbit_user and qbit_pass:
                            try:
                                auth_data = urllib.parse.urlencode({'username': qbit_user, 'password': qbit_pass}).encode('utf-8')
                                auth_req = urllib.request.Request(f"{qbit_url}/api/v2/auth/login", data=auth_data)
                                auth_res = urllib.request.urlopen(auth_req, context=ctx, timeout=3.0)
                                cookie = auth_res.getheader('Set-Cookie')
                            except Exception:
                                pass 
                        
                        mode_to_set = "1"
                        
                        if is_watching_global:
                            print(f"AUTOMATION ({node.get('title')}): Jellyfin playing! qBittorrent Throttled.")
                        else:
                            try:
                                pref_req = urllib.request.Request(f"{qbit_url}/api/v2/app/preferences")
                                if cookie: pref_req.add_header('Cookie', cookie)
                                pref_res = urllib.request.urlopen(pref_req, context=ctx, timeout=3.0)
                                prefs = json.loads(pref_res.read().decode())
                                
                                in_schedule = False
                                if prefs.get('scheduler_enabled', False):
                                    now = datetime.datetime.now()
                                    current_day = now.weekday() 
                                    yesterday = (current_day - 1) % 7
                                    sched_days = prefs.get('scheduler_days', 0)
                                    
                                    def matches_day(day_int, qbit_code):
                                        if qbit_code == 0: return True
                                        if qbit_code == 1 and day_int < 5: return True
                                        if qbit_code == 2 and day_int >= 5: return True
                                        if qbit_code - 3 == day_int: return True
                                        return False
                                        
                                    st = datetime.time(prefs.get('schedule_from_hour', 0), prefs.get('schedule_from_min', 0))
                                    et = datetime.time(prefs.get('schedule_to_hour', 0), prefs.get('schedule_to_min', 0))
                                    ct = now.time()
                                    
                                    is_overnight = st > et
                                    
                                    if matches_day(current_day, sched_days):
                                        if not is_overnight and st <= ct <= et:
                                            in_schedule = True
                                        elif is_overnight and ct >= st:
                                            in_schedule = True
                                            
                                    if matches_day(yesterday, sched_days) and is_overnight:
                                        if ct <= et:
                                            in_schedule = True
                                
                                if in_schedule:
                                    mode_to_set = "1"
                                    print(f"AUTOMATION ({node.get('title')}): Jellyfin stopped, but qBit Schedule is ACTIVE. Keeping throttled.")
                                else:
                                    mode_to_set = "0"
                                    print(f"AUTOMATION ({node.get('title')}): Jellyfin stopped & Schedule inactive. Restoring Full Speed.")
                            except Exception as e:
                                mode_to_set = "0" 
                                print(f"AUTOMATION ERROR ({node.get('title')} reading preferences): {e}")

                        mode_data = urllib.parse.urlencode({'mode': mode_to_set}).encode('utf-8')
                        mode_req = urllib.request.Request(f"{qbit_url}/api/v2/transfer/setSpeedLimitsMode", data=mode_data)
                        
                        if cookie: 
                            mode_req.add_header('Cookie', cookie)
                            
                        urllib.request.urlopen(mode_req, context=ctx, timeout=3.0)

                    except Exception as e:
                        print(f"AUTOMATION ERROR ({node.get('title')} VueTorrent throttle): {e}")

            was_watching_global = is_watching_global

if __name__ == "__main__":
    server_started = False
    active_server = None
    bound_ip = "0.0.0.0"

    # 1. Figure out which node we are on FIRST
    for group in DASHBOARD_CONFIG:
        if "bind_ip" in group:
            try:
                active_server = ThreadingHTTPServer((group["bind_ip"], NET['PORT']), HomerServer)
                ACTIVE_CERT = group.get("cert_path", "")
                
                # Assign the correct ID before threads start!
                LOCAL_NODE_ID = group["id"]
                bound_ip = group["bind_ip"]
                
                print(f"Detected Node: {group['title']} (IP: {bound_ip})")
                server_started = True
                break
            except OSError:
                continue

    # 2. Start the background threads NOW, so they use the correct LOCAL_NODE_ID
    threading.Thread(target=watch_file_changes, daemon=True).start()
    threading.Thread(target=auto_throttle_loop, daemon=True).start()
    threading.Thread(target=cert_swarm_loop, daemon=True).start()
    threading.Thread(target=background_status_updater, daemon=True).start()

    # 3. Finally, launch the web dashboard
    if server_started:
        print(f"Homer Swarm running at http://{bound_ip}:{NET['PORT']}")
        try:
            active_server.serve_forever()
        except KeyboardInterrupt: 
            pass
    else:
        print("Warning: Could not bind to any specific node IP. Falling back to 0.0.0.0")
        try:
            fallback_server = ThreadingHTTPServer(('0.0.0.0', NET['PORT']), HomerServer)
            print(f"Homer Swarm running at http://0.0.0.0:{NET['PORT']}")
            fallback_server.serve_forever()
        except KeyboardInterrupt: 
            pass