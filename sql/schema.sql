CREATE DATABASE IF NOT EXISTS sentinel
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sentinel;

CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    mac VARCHAR(17) NULL,
    role VARCHAR(100) NOT NULL,
    first_seen VARCHAR(32) NOT NULL,
    last_seen VARCHAR(32) NOT NULL,
    INDEX idx_devices_mac (mac),
    INDEX idx_devices_ip (ip)
) ENGINE=InnoDB;
