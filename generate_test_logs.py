#!/usr/bin/env python3
# -*- coding: utf-8-*-
"""
Script pour générer des fichiers de logs de test pour Anonyfiles
"""

import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_generic_logs(output_file: Path, num_lines: int = 100):
    """Génère des logs génériques avec des données sensibles."""

    users = ["john.doe", "alice.martin", "bob.smith", "emma.wilson", "charlie.brown"]
    ips = ["192.168.1.10", "10.0.0.45", "172.16.0.20", "192.168.1.100", "10.10.10.5"]
    emails = ["john.doe@example.com", "alice@company.com", "bob@test.org", "emma@email.com"]
    actions = ["LOGIN", "LOGOUT", "ACCESS", "ERROR", "WARNING", "INFO"]

    with open(output_file, 'w', encoding='utf-8') as f:
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(num_lines):
            timestamp = (base_time + timedelta(seconds=i*10)).strftime("%Y-%m-%d %H:%M:%S")
            user = random.choice(users)
            ip = random.choice(ips)
            action = random.choice(actions)

            if random.random() > 0.7:
                email = random.choice(emails)
                f.write(f"{timestamp} [{action}] User {user} from {ip} - Email: {email}\n")
            else:
                f.write(f"{timestamp} [{action}] User {user} from {ip}\n")

    print(f"✅ Logs génériques créés: {output_file} ({num_lines} lignes)")


def generate_apache_logs(output_file: Path, num_lines: int = 100):
    """Génère des logs Apache avec des IPs et User-Agents."""

    ips = ["203.0.113.45", "198.51.100.23", "192.0.2.150", "203.0.113.78", "198.51.100.99"]
    paths = ["/index.html", "/admin/login", "/api/users", "/images/logo.png", "/css/style.css"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    status_codes = [200, 201, 301, 302, 400, 401, 403, 404, 500]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) Firefox/95.0"
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(num_lines):
            timestamp = (base_time + timedelta(seconds=i*5)).strftime("%d/%b/%Y:%H:%M:%S +0000")
            ip = random.choice(ips)
            method = random.choice(methods)
            path = random.choice(paths)
            status = random.choice(status_codes)
            size = random.randint(100, 50000)
            ua = random.choice(user_agents)

            f.write(f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size} "-" "{ua}"\n')

    print(f"✅ Logs Apache créés: {output_file} ({num_lines} lignes)")


def generate_splunk_logs(output_file: Path, num_lines: int = 100):
    """Génère des logs au format Splunk."""

    hosts = ["server01.example.com", "db-prod.company.local", "web-app-01", "api-gateway"]
    sources = ["/var/log/application.log", "/var/log/security.log", "/opt/app/logs/error.log"]
    severities = ["INFO", "WARN", "ERROR", "DEBUG", "CRITICAL"]
    users = ["admin", "service_account", "app_user", "backup_user"]
    ips = ["10.20.30.40", "172.31.10.5", "192.168.100.50"]

    with open(output_file, 'w', encoding='utf-8') as f:
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(num_lines):
            timestamp = (base_time + timedelta(seconds=i*8)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
            host = random.choice(hosts)
            source = random.choice(sources)
            severity = random.choice(severities)
            user = random.choice(users)
            ip = random.choice(ips)

            f.write(f'{timestamp} host={host} source="{source}" severity={severity} user={user} src_ip={ip} message="User {user} performed action from {ip}"\n')

    print(f"✅ Logs Splunk créés: {output_file} ({num_lines} lignes)")


def generate_system_logs(output_file: Path, num_lines: int = 100):
    """Génère des logs système Linux."""

    services = ["sshd", "systemd", "kernel", "NetworkManager", "cron"]
    hosts = ["prod-server", "backup-node", "web-frontend"]
    pids = [str(random.randint(1000, 9999)) for _ in range(10)]
    users = ["root", "admin", "webuser", "dbadmin"]
    ips = ["192.168.50.10", "10.0.100.25", "172.20.1.5"]

    with open(output_file, 'w', encoding='utf-8') as f:
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(num_lines):
            timestamp = (base_time + timedelta(seconds=i*15)).strftime("%b %d %H:%M:%S")
            host = random.choice(hosts)
            service = random.choice(services)
            pid = random.choice(pids)

            if service == "sshd":
                user = random.choice(users)
                ip = random.choice(ips)
                f.write(f"{timestamp} {host} {service}[{pid}]: Accepted publickey for {user} from {ip} port 22 ssh2\n")
            else:
                f.write(f"{timestamp} {host} {service}[{pid}]: Service started successfully\n")

    print(f"✅ Logs système créés: {output_file} ({num_lines} lignes)")


def main():
    """Génère tous les fichiers de logs de test."""

    # Crée le dossier de sortie
    output_dir = Path("test_logs")
    output_dir.mkdir(exist_ok=True)

    print("🚀 Génération des fichiers de logs de test...\n")

    # Génère différents types de logs
    generate_generic_logs(output_dir / "generic_app.log", 150)
    generate_apache_logs(output_dir / "apache_access.log", 200)
    generate_splunk_logs(output_dir / "splunk_events.log", 120)
    generate_system_logs(output_dir / "syslog.log", 100)

    # Crée aussi quelques fichiers supplémentaires
    generate_generic_logs(output_dir / "app_errors.log", 50)
    generate_apache_logs(output_dir / "nginx_access.log", 80)

    print(f"\n✨ Tous les fichiers ont été générés dans: {output_dir.absolute()}")
    print(f"\n📋 Pour tester avec l'interface TUI:")
    print(f"   anonyfiles-cli logs interactive")
    print(f"\n📋 Pour tester en ligne de commande:")
    print(f"   anonyfiles-cli logs anonymize {output_dir} --profile generic_logs --output {output_dir}_anonymized")


if __name__ == "__main__":
    main()
