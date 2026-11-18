"""Store Sentinel device discoveries in MySQL."""

import os
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection
from dotenv import load_dotenv


load_dotenv()


def database_config() -> dict[str, Any]:
    """Read MySQL connection settings from environment variables."""
    return {
        "host": os.getenv("SENTINEL_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("SENTINEL_DB_PORT", "3306")),
        "user": os.getenv("SENTINEL_DB_USER", "sentinel"),
        "password": os.getenv("SENTINEL_DB_PASSWORD", ""),
        "database": os.getenv("SENTINEL_DB_NAME", "sentinel"),
    }


def connect() -> MySQLConnection:
    """Open a connection to the configured MySQL database."""
    return mysql.connector.connect(**database_config())


def normalize_mac(mac: str | None) -> str | None:
    """Store MAC addresses consistently and keep missing values as NULL."""
    if not mac:
        return None
    return mac.strip().upper()


def ensure_schema(connection: MySQLConnection) -> None:
    """Create the devices table and indexes when they do not exist."""
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(45) NOT NULL,
            mac VARCHAR(17) NULL,
            role VARCHAR(100) NOT NULL,
            first_seen VARCHAR(32) NOT NULL,
            last_seen VARCHAR(32) NOT NULL,
            INDEX idx_devices_mac (mac),
            INDEX idx_devices_ip (ip)
        ) ENGINE=InnoDB
        """
    )
    connection.commit()
    cursor.close()


def save_scan(devices: list[dict[str, str]], scanned_at: str) -> None:
    """Save one scan and update existing devices by MAC or unknown-device IP."""
    connection = connect()
    try:
        ensure_schema(connection)
        cursor = connection.cursor()
        for device in devices:
            ip = device["ip"]
            mac = normalize_mac(device.get("mac"))
            role = device.get("role", "unknown device")

            if mac:
                cursor.execute(
                    "SELECT id FROM devices WHERE mac = %s ORDER BY id LIMIT 1",
                    (mac,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id FROM devices
                    WHERE ip = %s AND mac IS NULL
                    ORDER BY id LIMIT 1
                    """,
                    (ip,),
                )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE devices
                    SET ip = %s, mac = %s, role = %s, last_seen = %s
                    WHERE id = %s
                    """,
                    (ip, mac, role, scanned_at, existing[0]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO devices (ip, mac, role, first_seen, last_seen)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (ip, mac, role, scanned_at, scanned_at),
                )
        connection.commit()
        cursor.close()
    finally:
        connection.close()


def list_devices() -> list[dict[str, str | None]]:
    """Return all devices saved so far."""
    connection = connect()
    try:
        ensure_schema(connection)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT ip, mac, role, first_seen, last_seen "
            "FROM devices ORDER BY ip"
        )
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]
    finally:
        connection.close()
