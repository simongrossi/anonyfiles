import random
import time
from datetime import datetime, timedelta
import argparse
from pathlib import Path

# Constantes pour la simulation
LEVELS = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"]
COMPONENTS = [
    "API",
    "Auth",
    "DB",
    "Payment",
    "UI",
    "Worker",
    "Cache",
    "EmailService",
    "Audit",
]
MESSAGES = {
    "INFO": [
        "User logged in successfully",
        "Request processed in {ms}ms",
        "Cache refreshed",
        "Job started",
        "Job finished",
        "Health check passed",
        "Connection established",
    ],
    "WARNING": [
        "High memory usage detected",
        "Response time > 500ms",
        "Rate limit approaching for user {user_id}",
        "Deprecated API usage",
        "Disk space low (20% remaining)",
    ],
    "ERROR": [
        "Database connection failed",
        "Payment gateway timeout",
        "NullReferenceException in handler",
        "File not found: {file}",
        "Failed to send email to {email}",
    ],
    "DEBUG": [
        "Variable x = {val}",
        "Entering function process_data()",
        "Query: SELECT * FROM users WHERE id={id}",
        "Payload size: {size} bytes",
        "Parsing config options",
    ],
    "CRITICAL": [
        "System crash imminent",
        "Data corruption detected in sector {sector}",
        "Security breach attempt blocked",
        "Main service loop terminated unexpectedly",
    ],
}


def generate_log_line(format_type: str, timestamp: datetime) -> str:
    level = random.choices(LEVELS, weights=[50, 20, 10, 15, 5], k=1)[0]
    component = random.choice(COMPONENTS)
    msg_template = random.choice(MESSAGES[level])

    # Remplissage des templates avec des valeurs aléatoires
    message = msg_template.format(
        ms=random.randint(10, 2000),
        user_id=random.randint(1000, 9999),
        file=f"file_{random.randint(1, 100)}.txt",
        email=f"user{random.randint(1, 100)}@example.com",
        val=random.randint(0, 100),
        id=random.randint(1, 10000),
        size=random.randint(100, 5000),
        sector=random.randint(100, 999),
    )

    if format_type == "syslog":
        # Format Syslog : MMM DD HH:MM:SS hostname app[pid]: message
        month = timestamp.strftime("%b")
        day = timestamp.day
        ts_str = timestamp.strftime("%H:%M:%S")
        return f"{month} {day:2d} {ts_str} localhost {component.lower()}[{random.randint(1000,9999)}]: {level} - {message}"

    elif format_type == "apache":
        # Format Apache Combined simplifié
        ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
        ts_str = timestamp.strftime("%d/%b/%Y:%H:%M:%S %z")
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        path = f"/api/v1/{component.lower()}"
        status = random.choice([200, 201, 304, 400, 401, 403, 404, 500, 502])
        size = random.randint(100, 10000)
        return f'{ip} - - [{ts_str}] "{method} {path} HTTP/1.1" {status} {size} "-" "Mozilla/5.0"'

    else:  # standard / application
        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"{ts_str} [{level}] {component}: {message}"


def main():
    parser = argparse.ArgumentParser(description="Générateur de logs de test")
    parser.add_argument(
        "--output", "-o", type=str, default="test.log", help="Fichier de sortie"
    )
    parser.add_argument(
        "--count", "-n", type=int, default=1000, help="Nombre de lignes à générer"
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["standard", "syslog", "apache"],
        default="standard",
        help="Format des logs",
    )
    parser.add_argument(
        "--live",
        "-l",
        action="store_true",
        help="Mode live : génère des logs indéfiniment (CTRL+C pour arrêter)",
    )
    parser.add_argument(
        "--rate",
        "-r",
        type=float,
        default=1.0,
        help="Nombre de logs par seconde (mode live uniquement)",
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    # Création du dossier parent si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Génération de logs dans {output_path} (Format: {args.format})...")

    current_time = datetime.now() - timedelta(
        hours=24
    )  # Start 24h ago for static generation

    if args.live:
        print(
            f"Mode LIVE activé ({args.rate} logs/sec). Appuyez sur CTRL+C pour arrêter."
        )
        try:
            with open(output_path, "a", encoding="utf-8") as f:
                while True:
                    line = generate_log_line(args.format, datetime.now())
                    f.write(line + "\n")
                    f.flush()
                    print(line)  # Echo to console
                    time.sleep(1.0 / args.rate)
        except KeyboardInterrupt:
            print("\nArrêt de la génération.")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            for i in range(args.count):
                # Incrémenter le temps pour que ça paraisse réaliste sur 24h
                current_time += timedelta(seconds=86400 / args.count)
                line = generate_log_line(args.format, current_time)
                f.write(line + "\n")
        print(f"{args.count} lignes générées avec succès.")


if __name__ == "__main__":
    main()
