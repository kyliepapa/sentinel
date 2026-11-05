<<<<<<< HEAD
# IoT Sentinel

IoT Sentinel is a small, defensive network-monitoring project. It discovers devices on a private local network that the project team owns or has permission to monitor.

## First milestone

Given a private subnet such as `192.168.1.0/24`, Sentinel sends ARP requests and reports responding devices:

- IP address
- MAC address
- discovery time

The first milestone is read-only. It does not log in to devices, inspect traffic, or scan the public internet.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Only scan a private network you own or have permission to monitor:

```powershell
python scanner.py 192.168.1.0/24 --router-ip 192.168.1.1 --camera-ip 192.168.1.20 --laptop-ip 192.168.1.25
```

The IP addresses above are examples. Replace them with the addresses from `ipconfig` and the router's device list. You can also provide `--router-mac`, `--camera-mac`, and `--laptop-mac`. The script labels matching devices as `router`, `camera`, or `laptop`; others are `unknown device`.

Every scan is also saved to `data/sentinel.db` so Sentinel can remember when a device was first and last seen. To use a different database file, add `--database path/to/file.db`.

## Team safety rule

Do not run the scanner against the internet, another person's network, or a subnet without permission. Use the router's device list as the reference when verifying results.
=======
# sentinel
# Initial Goal: The Sentinel scans your network to see what devices are on it and lists them for the user to view. The user can designate certain devices as familiar or safe, then turn on a setting where the user is notified about any new or unfamiliar devices, and provide the user with instructions to remove them from the network if they'd like
# Stretch Goal: Add built-in tools to deal with unfamiliar devices
>>>>>>> eb30d080f0b13669b2c8f759703e4d43d3d089b0
