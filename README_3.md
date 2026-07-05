# 👻 Ghost in the LAN (Windows Setup)

Detects new/unrecognized devices on your WiFi and emails you an alert when a "ghost" joins your network.

## 1. Install prerequisites

1. **Python 3.9+** — https://www.python.org/downloads/ (check "Add Python to PATH" during install)
2. **Nmap** — https://nmap.org/download.html
   - Run the Windows installer.
   - Make sure the **Npcap** checkbox is selected during install (this is what lets Nmap see MAC addresses).
3. Confirm both are on your PATH by opening a new terminal (PowerShell or cmd) and running:
   ```
   python --version
   nmap --version
   ```

## 2. Find your subnet

Run `ipconfig` in a terminal and look for your WiFi adapter's "IPv4 Address" and "Subnet Mask".
If your IP is `192.168.1.42` with mask `255.255.255.0`, your subnet is `192.168.1.0/24`.
Update the `SUBNET` variable at the top of `ghost_in_the_lan.py` if it's different.

## 3. Run your first scan

**Important: MAC address detection requires Administrator privileges on Windows.**
Right-click your terminal (PowerShell/cmd/Windows Terminal) and choose **"Run as administrator"**, then:

```
cd path\to\network_monitor
python ghost_in_the_lan.py --scan-once
```

This prints every device found, tagged `UNKNOWN` (since `known_devices.json` starts empty).

## 4. Mark your own devices as "known"

Open `known_devices.json` and add your own devices, matching the MAC addresses printed in step 3:

```json
{
  "aa:bb:cc:dd:ee:ff": "My iPhone",
  "11:22:33:44:55:66": "Living Room Smart TV",
  "de:ad:be:ef:00:01": "My Laptop"
}
```

Run `--scan-once` again — everything you added should no longer say `UNKNOWN`.

## 5. Set up email alerts (optional but recommended)

1. Go to https://myaccount.google.com/apppasswords (requires 2-Step Verification enabled on your Google account).
2. Generate an "app password" for "Mail".
3. In `ghost_in_the_lan.py`, set:
   ```python
   EMAIL_ENABLED = True
   EMAIL_FROM = "your_email@gmail.com"
   EMAIL_PASSWORD = "the 16-character app password"
   EMAIL_TO = "your_email@gmail.com"
   ```
4. Run `--scan-once` again to test — you shouldn't get an email unless there's actually an unknown device. To force a test, temporarily rename a MAC in `known_devices.json`.

## 6. Run continuously

Without `--scan-once`, the script loops forever, scanning every `INTERVAL_MINUTES` (default 5):

```
python ghost_in_the_lan.py
```

Leave this terminal (as Administrator) running in the background. Logs go to both the console and `ghost_log.txt`.

### Running it automatically at startup (optional)

Use **Task Scheduler**:
1. Open Task Scheduler → Create Task
2. General tab: check "Run with highest privileges" (needed for MAC detection)
3. Triggers tab: "At log on"
4. Actions tab: Program = `python`, Arguments = `ghost_in_the_lan.py`, "Start in" = your project folder
5. Save.

## Notes

- If you ever move this to a Raspberry Pi later, the script is identical — just install Nmap via `sudo apt install nmap` and run it with `sudo` (Linux doesn't need Npcap).
- Devices that are asleep or have WiFi randomization/private MAC address features enabled (common on modern phones) may show up with a different MAC each time — you may need to disable "private WiFi address" for your own phone in its WiFi settings so it matches consistently.
