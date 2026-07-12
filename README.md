# 👻 Ghost in the LAN

A lightweight, automated network security monitor that acts as a tripwire for your local WiFi. It continuously audits your subnet for unauthorized devices and instantly dispatches an email alert the second an unrecognized MAC address ("a ghost") connects.

---

## 🚀 Core Features

* **🕵️ Automated Intruder Detection:** Scans your network using high-precision Nmap discovery to capture active MAC addresses.
* **📧 Instant Threat Alerting:** Connects securely via SMTP to shoot you an immediate email warning when an unknown device breaches the network.
* **📝 Local Logging System:** Maintains a running ledger (`ghost_log.txt`) alongside console outputs for continuous activity tracking.
* **📂 Known Device Whitelisting:** Simple JSON configuration mapping trusted devices so you only get alerted for actual anomalies.

---

## 🛠️ Prerequisites & Installation

### 1. Engine Setup

* **Python 3.9+** — Ensure you check **"Add Python to PATH"** during installation.
* **Nmap Engine** — Run the Windows installer and make sure **Npcap** is checked (essential for MAC address capturing on Windows).

Verify both environments are active via terminal:

```bash
python --version
nmap --version

```

### 2. Network Alignment

Run `ipconfig` to discover your WiFi adapter's IPv4 address and Subnet Mask.

* *Example:* If your IP is `192.168.1.42` and mask is `255.255.255.0`, your subnet target is `192.168.1.0/24`.
* Update the `SUBNET` parameter at the top of `ghost_in_the_lan.py` accordingly.

---

## ⚙️ Configuration & Execution

### Step 1: Initialize & Scan Network

Open an **Administrative Terminal** (Right-click PowerShell/CMD → *Run as Administrator*) and map the network:

```bash
cd path\to\network_monitor
python ghost_in_the_lan.py --scan-once

```

*This performs an isolated initial scan, highlighting all connected hosts as `UNKNOWN`.*

### Step 2: Provision Whitelist

Open the automatically generated `known_devices.json` and append your trusted network hardware:

```json
{
  "aa:bb:cc:dd:ee:ff": "My iPhone",
  "11:22:33:44:55:66": "Living Room Smart TV",
  "de:ad:be:ef:00:01": "My Laptop"
}

```

*Re-run `--scan-once` to confirm your whitelisted assets register as recognized.*

### Step 3: Configure SMTP Email Alerts (Optional)

1. Head to [Google App Passwords](https://myaccount.google.com/apppasswords) *(Requires 2FA active)*.
2. Generate an app-specific string for "Mail".
3. Update the credential block inside `ghost_in_the_lan.py`:

```python
EMAIL_ENABLED = True
EMAIL_FROM = "your_email@gmail.com"
EMAIL_PASSWORD = "your-16-character-app-password"
EMAIL_TO = "your_email@gmail.com"

```

---

## 🏃 Deployment Modes

### Manual Background Execution

To run the script indefinitely on a standard looping interval (default: 5 minutes):

```bash
python ghost_in_the_lan.py

```

### Automated Windows Persistence (Task Scheduler)

To ensure the monitor runs silently at system startup:

1. Launch **Windows Task Scheduler** $\rightarrow$ **Create Task**.
2. **General Tab:** Toggle `Run with highest privileges` *(Crucial for raw packet/MAC parsing)*.
3. **Triggers Tab:** Set to `At log on`.
4. **Actions Tab:** Action: `Start a program` | Program: `python` | Arguments: `ghost_in_the_lan.py` | Start in: `Your project absolute directory`.

---

## 💡 Operational Notes

* **Linux/Raspberry Pi Portability:** The code core is fully cross-platform. To port to a Pi, simply run `sudo apt install nmap` and execute the script using `sudo python3`.
* **MAC Randomization:** Modern iOS/Android privacy flags ("Private Wi-Fi Address") shift MAC addresses dynamically. For flawless tracking, toggle off private MAC addresses for your home network profile.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for further details.
