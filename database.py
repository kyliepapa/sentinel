"""Store Sentinel device discoveries in a local SQLite database."""

import sqlite3
from pathlib import Path


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
        for device in devices:
            connection.execute(
                """
                INSERT INTO devices (ip, mac, role, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ip, mac) DO UPDATE SET
                    role = excluded.role,
                    last_seen = excluded.last_seen
                """,
                (
                    device["ip"],
                    device.get("mac"),
                    device.get("role", "unknown device"),
                    scanned_at,
                    scanned_at,
                ),
            )


def list_devices(database_path: str) -> list[dict[str, str]]:
    """Return all devices saved so far."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT ip, mac, role, first_seen, last_seen FROM devices ORDER BY ip"
        ).fetchall()
    return [dict(row) for row in rows]
