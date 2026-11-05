"""Discover and label devices on a private subnet using Nmap."""

import argparse
import ipaddress
import json
import subprocess
from datetime import datetime, timezone
from xml.etree import ElementTree

from database import save_scan


def validate_private_subnet(value: str) -> str:
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "enter a valid IPv4 subnet, such as 192.168.1.0/24"
        ) from exc
    if network.version != 4 or not network.is_private:
        raise argparse.ArgumentTypeError("only private IPv4 subnets are allowed")
    return str(network)


def discover_devices(subnet: str, timeout: int = 5) -> list[dict[str, str]]:
    """Run Nmap host discovery and parse its XML output."""
    command = [
        "nmap", "-sn", "-PR", "-T3", "--host-timeout", f"{timeout}s",
        "-oX", "-", subnet,
    ]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Nmap was not found. Install Nmap and make sure it is on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or "Nmap could not complete the scan.") from exc

    root = ElementTree.fromstring(completed.stdout)
    devices = []
    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.get("state") != "up":
            continue
        addresses = {
            address.get("addrtype"): address.get("addr")
            for address in host.findall("address")
        }
        device = {"ip": addresses.get("ipv4", "unknown")}
        if addresses.get("mac"):
            device["mac"] = addresses["mac"]
        devices.append(device)
    return devices


def label_devices(devices: list[dict[str, str]], known: dict[str, dict[str, str]]) -> None:
    """Label a device when its known IP or MAC matches."""
    for device in devices:
        device["role"] = "unknown device"
        for role, identity in known.items():
            same_ip = identity.get("ip") == device.get("ip")
            known_mac = (identity.get("mac") or "").lower()
            device_mac = (device.get("mac") or "").lower()
            same_mac = bool(known_mac) and known_mac == device_mac
            if (identity.get("ip") and same_ip) or (identity.get("mac") and same_mac):
                device["role"] = role
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover devices on a private subnet")
    parser.add_argument("subnet", type=validate_private_subnet)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--database", default="data/sentinel.db")
    for role in ("router", "camera", "laptop"):
        parser.add_argument(f"--{role}-ip", help=f"known {role} IP address")
        parser.add_argument(f"--{role}-mac", help=f"known {role} MAC address")
    args = parser.parse_args()

    devices = discover_devices(args.subnet, timeout=args.timeout)
    known = {
        role: {
            "ip": getattr(args, f"{role}_ip"),
            "mac": getattr(args, f"{role}_mac"),
        }
        for role in ("router", "camera", "laptop")
    }
    label_devices(devices, known)
    scanned_at = datetime.now(timezone.utc).isoformat()
    save_scan(args.database, devices, scanned_at)
    print(json.dumps({
        "subnet": args.subnet,
        "discovered_at": scanned_at,
        "database": args.database,
        "devices": devices,
    }, indent=2))


if __name__ == "__main__":
    main()
