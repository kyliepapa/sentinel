# IoT Sentinel

IoT Sentinel is a small, defensive network-monitoring project. It discovers devices on a private local network that the project team owns or has permission to monitor.

## Project goals

The initial goal is to scan the local network, list the devices found, and let the user designate familiar or safe devices. A future feature will notify the user about new or unfamiliar devices and provide instructions for removing them from the network.

The stretch goal is to add built-in tools for dealing with unfamiliar devices.

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

Start the local dashboard from the `sentinel` folder:

```powershell
py server.py
```

Then open <http://127.0.0.1:8000>. The dashboard reads the devices saved in
`data/sentinel.db` through the `/api/devices` endpoint. Run the scanner in a
second terminal when you want to update the database, then click **Refresh data**.

Only scan a private network you own or have permission to monitor:

```powershell
python scanner.py 192.168.1.0/24 --router-ip 192.168.1.1 --camera-ip 192.168.1.20 --laptop-ip 192.168.1.25
```

The IP addresses above are examples. Replace them with the addresses from `ipconfig` and the router's device list. You can also provide `--router-mac`, `--camera-mac`, and `--laptop-mac`. The script labels matching devices as `router`, `camera`, or `laptop`; others are `unknown device`.

Every scan is also saved to `data/sentinel.db` so Sentinel can remember when a device was first and last seen. To use a different database file, add `--database path/to/file.db`.

## Team safety rule

Do not run the scanner against the internet, another person's network, or a subnet without permission. Use the router's device list as the reference when verifying results.
