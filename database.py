"""Store Sentinel device discoveries in a local SQLite database."""

import sqlite3
from pathlib import Path


def normalize_mac(mac: str | None) -> str | None:
    """Store MAC addresses consistently and keep missing values as NULL."""
    if not mac:
        return None
    return mac.strip().upper()


def remove_duplicate_unknowns(connection: sqlite3.Connection) -> None:
    """Keep one row per IP when older scans saved a missing MAC repeatedly."""
    connection.execute(
        """
        DELETE FROM devices
        WHERE mac IS NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM devices
              WHERE mac IS NULL
              GROUP BY ip
          )
        """
    )


def save_scan(database_path: str, devices: list[dict[str, str]], scanned_at: str) -> None:
    """Create the table if needed and save the devices found in one scan."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                mac TEXT,
                role TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                UNIQUE(ip, mac)
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac)")
        remove_duplicate_unknowns(connection)

        for device in devices:
            ip = device["ip"]
            mac = normalize_mac(device.get("mac"))
            role = device.get("role", "unknown device")

            # A MAC address is the best identity. If it is unavailable,
            # reuse the existing unknown row for that IP instead of creating
            # another duplicate on every scan.
            if mac:
                existing = connection.execute(
                    "SELECT id FROM devices WHERE mac = ? ORDER BY id LIMIT 1",
                    (mac,),
                ).fetchone()
            else:
                existing = connection.execute(
                    "SELECT id FROM devices WHERE ip = ? AND mac IS NULL ORDER BY id LIMIT 1",
                    (ip,),
                ).fetchone()

            if existing:
                connection.execute(
                    """
                    UPDATE devices
                    SET ip = ?, mac = ?, role = ?, last_seen = ?
                    WHERE id = ?
                    """,
                    (ip, mac, role, scanned_at, existing[0]),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO devices (ip, mac, role, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (ip, mac, role, scanned_at, scanned_at),
                )


def list_devices(database_path: str) -> list[dict[str, str]]:
    """Return all devices saved so far."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT ip, mac, role, first_seen, last_seen FROM devices ORDER BY ip"
        ).fetchall()
    return [dict(row) for row in rows]
