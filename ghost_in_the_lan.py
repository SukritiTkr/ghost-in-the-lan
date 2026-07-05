"""
Ghost in the LAN
----------------------------
Scans your LAN for connected devices, compares them against a list of
"known" devices, and sends an email alert when an unrecognized device
(new MAC address) appears — a ghost on your network.

Requires:
  - Nmap installed (https://nmap.org/download.html)
  - Npcap installed (https://npcap.com/) so Nmap can see MAC addresses on Windows
  - Run as Administrator (MAC address detection needs raw socket / packet capture access)
  - pip install -r requirements.txt

Usage:
  python ghost_in_the_lan.py --scan-once      # single scan, print results, exit
  python ghost_in_the_lan.py                  # loop forever, scanning every INTERVAL_MINUTES
"""

import argparse
import json
import os
import smtplib
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText

# --------------------------------------------------------------------------
# CONFIG — edit these values for your setup
# --------------------------------------------------------------------------

SUBNET = "192.168.1.0/24"          # your LAN subnet — check with `ipconfig`
INTERVAL_MINUTES = 5                # how often to scan when running in a loop
KNOWN_DEVICES_FILE = "known_devices.json"
LOG_FILE = "ghost_log.txt"

# Email alert settings (Gmail example — use an "app password", not your real password)
EMAIL_ENABLED = False                # flip to True once configured
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "your_email@gmail.com"
EMAIL_PASSWORD = "your_16_char_app_password"   # generate at https://myaccount.google.com/apppasswords
EMAIL_TO = "your_email@gmail.com"              # where alerts get sent (can be same address)

# --------------------------------------------------------------------------


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_known_devices() -> dict:
    """Returns {mac_address_lowercase: nickname}"""
    if not os.path.exists(KNOWN_DEVICES_FILE):
        log(f"No {KNOWN_DEVICES_FILE} found — creating an empty one.")
        with open(KNOWN_DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    with open(KNOWN_DEVICES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {mac.lower(): nickname for mac, nickname in data.items()}


def save_known_devices(devices: dict):
    with open(KNOWN_DEVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=2)


def scan_network(subnet: str) -> list:
    """
    Runs `nmap -sn <subnet>` with XML output and parses it for
    IP, MAC address, and vendor. Requires admin privileges for MAC detection.
    Returns a list of dicts: [{ "ip": ..., "mac": ..., "vendor": ..., "hostname": ... }, ...]
    """
    cmd = ["nmap", "-sn", "-oX", "-", subnet]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, check=True
        )
    except FileNotFoundError:
        log("ERROR: nmap not found. Install it from https://nmap.org/download.html "
            "and make sure it's on your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        log(f"ERROR: nmap failed: {e.stderr}")
        return []
    except subprocess.TimeoutExpired:
        log("ERROR: nmap scan timed out.")
        return []

    devices = []
    root = ET.fromstring(result.stdout)
    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.get("state") != "up":
            continue

        ip = None
        mac = None
        vendor = None
        for addr in host.findall("address"):
            addrtype = addr.get("addrtype")
            if addrtype == "ipv4":
                ip = addr.get("addr")
            elif addrtype == "mac":
                mac = addr.get("addr")
                vendor = addr.get("vendor") or "Unknown vendor"

        hostname_el = host.find("hostnames/hostname")
        hostname = hostname_el.get("name") if hostname_el is not None else ""

        if mac:  # skip entries where we couldn't get a MAC (often the scanning host itself)
            devices.append({
                "ip": ip,
                "mac": mac.lower(),
                "vendor": vendor,
                "hostname": hostname,
            })

    return devices


def send_email_alert(unknown_devices: list):
    if not EMAIL_ENABLED:
        log("Email alerts disabled (EMAIL_ENABLED=False) — skipping send.")
        return

    lines = ["The following unrecognized device(s) joined your network:\n"]
    for d in unknown_devices:
        lines.append(f"  MAC: {d['mac']}  IP: {d['ip']}  Vendor: {d['vendor']}  Hostname: {d['hostname']}")
    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"👻 Ghost in the LAN — unknown device detected ({len(unknown_devices)})"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        log("Email alert sent.")
    except Exception as e:
        log(f"ERROR sending email: {e}")


def run_scan_cycle(known_devices: dict):
    log(f"Scanning {SUBNET} ...")
    devices = scan_network(SUBNET)
    log(f"Found {len(devices)} device(s) with MAC addresses.")

    unknown = [d for d in devices if d["mac"] not in known_devices]

    for d in devices:
        tag = known_devices.get(d["mac"], "UNKNOWN")
        log(f"  {d['ip']:<15} {d['mac']} {d['vendor'] or '':<20} -> {tag}")

    if unknown:
        log(f"👻 {len(unknown)} ghost(s) detected on your LAN!")
        send_email_alert(unknown)
    else:
        log("No ghosts here. All devices recognized.")

    return devices


def main():
    parser = argparse.ArgumentParser(description="Ghost in the LAN — home network device monitor")
    parser.add_argument("--scan-once", action="store_true",
                         help="Run a single scan and exit (don't loop)")
    args = parser.parse_args()

    known_devices = load_known_devices()

    if not known_devices:
        log("Your known_devices.json is empty. Run with --scan-once, "
            "then copy MAC addresses you recognize into known_devices.json "
            "with a nickname, e.g.:")
        log('  { "aa:bb:cc:dd:ee:ff": "My iPhone" }')

    if args.scan_once:
        run_scan_cycle(known_devices)
        return

    log(f"Starting continuous monitoring (every {INTERVAL_MINUTES} min). Ctrl+C to stop.")
    try:
        while True:
            run_scan_cycle(known_devices)
            time.sleep(INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        log("Stopped by user.")


if __name__ == "__main__":
    main()
