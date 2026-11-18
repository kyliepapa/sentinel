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

Create the MySQL database and table using `sql/schema.sql`. Then copy
`.env.example` to `.env` and set the MySQL username and password. The
application reads these settings from environment variables.

For a dedicated local user, run these statements in MySQL as an administrator,
using the same password you put in `.env`:

```sql
CREATE USER 'sentinel'@'127.0.0.1' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON sentinel.* TO 'sentinel'@'127.0.0.1';
FLUSH PRIVILEGES;
```

## Run

Start the local dashboard from the project root:

```powershell
py -m app.server
```

Then open <http://127.0.0.1:8000>. The dashboard reads the devices saved in
MySQL through the `/api/devices` endpoint. Run the scanner in a
second terminal when you want to update the database, then click **Refresh data**.
The dashboard displays only devices from the most recent scan; older device
records remain in the database for history but are not shown as current.

Only scan a private network you own or have permission to monitor:

```powershell
python -m app.scanner 192.168.1.0/24 --router-ip 192.168.1.1 --camera-ip 192.168.1.20 --laptop-ip 192.168.1.25
```

The IP addresses above are examples. Replace them with the addresses from `ipconfig` and the router's device list. You can also provide `--router-mac`, `--camera-mac`, and `--laptop-mac`. The script labels matching devices as `router`, `camera`, or `laptop`; others are `unknown device`.

Every scan is saved to MySQL so Sentinel can remember when a device was first
and last seen. Configure a different MySQL server or database by changing the
values in `.env`.

## Team safety rule

Do not run the scanner against the internet, another person's network, or a subnet without permission. Use the router's device list as the reference when verifying results.
