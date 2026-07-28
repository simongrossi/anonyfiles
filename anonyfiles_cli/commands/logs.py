import logging
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table


from anonyfiles_cli.utils.default_paths import get_default_log_dir

# Initialisation du logger et de la console
logger = logging.getLogger(__name__)
console = Console()

# Profils de configuration prêts à l'emploi pour l'anonymisation de journaux
# applicatifs ou d'équipements (Apache, Splunk, Tenable, Tufin…).
PROFILES_DIR = Path(__file__).parent.parent / "log_profiles"

# Définition de l'application Typer
app = typer.Typer(help="Gestion et analyse des fichiers de logs.")


@app.command("list-profiles")
def list_profiles():
    """Lister les profils de configuration disponibles pour anonymiser des logs."""
    profile_files = sorted(PROFILES_DIR.glob("*.yaml"))

    if not profile_files:
        console.print(f"[yellow]Aucun profil trouvé dans {PROFILES_DIR}.[/]")
        return

    table = Table(title="Profils de logs disponibles")
    table.add_column("Profil", style="cyan", no_wrap=True)
    table.add_column("Description")

    for profile_path in profile_files:
        try:
            with open(profile_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            description = data.get("description", "—")
        except (OSError, yaml.YAMLError) as e:
            description = f"[red]Profil illisible : {e}[/red]"
        table.add_row(profile_path.stem, description)

    console.print(table)
    console.print(
        "\nUtilisation : [cyan]anonyfiles-cli anonymize <fichier> "
        "--config anonyfiles_cli/log_profiles/<profil>.yaml[/]"
    )


@app.command("list")
def list_logs():
    """Lister les fichiers de logs disponibles."""
    log_dir = get_default_log_dir()

    if not log_dir.exists():
        console.print(f"[yellow]Le dossier de logs {log_dir} n'existe pas encore.[/]")
        return

    files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.jsonl"))
    if not files:
        console.print("[yellow]Aucun fichier de log trouvé.[/]")
        return

    console.print(f"[bold]Fichiers de logs dans {log_dir} :[/]")
    for log_file in sorted(files):
        size_kb = log_file.stat().st_size / 1024
        console.print(f" - [cyan]{log_file.name}[/] ({size_kb:.1f} KB)")


@app.command("interactive")
def interactive_viewer():
    """Lancer l'interface TUI interactive pour explorer les logs."""
    try:
        from anonyfiles_cli.tui import LogsApp
    except ImportError:
        console.print(
            "[bold red]Erreur:[/bold red] Textual n'est pas installé. Veuillez l'installer avec :"
        )
        console.print("pip install textual")
        raise typer.Exit(code=1)

    log_dir = get_default_log_dir()

    # Créer le dossier s'il n'existe pas pour éviter le crash de l'app
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Dossier de logs créé : {log_dir}[/]")
        except Exception as e:
            console.print(f"[red]Impossible de créer le dossier de logs : {e}[/]")
            raise typer.Exit(code=1)

    app_tui = LogsApp(log_dir)
    app_tui.run()


@app.command("clear")
def clear_logs(
    force: bool = typer.Option(
        False, "--force", "-f", help="Forcer la suppression sans confirmation"
    ),
):
    """Supprimer tous les fichiers de logs."""
    log_dir = get_default_log_dir()

    if not log_dir.exists():
        console.print("[yellow]Rien à supprimer.[/]")
        return

    files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.jsonl"))
    if not files:
        console.print("[yellow]Le dossier est déjà vide.[/]")
        return

    if not force:
        confirm = typer.confirm(
            f"Voulez-vous vraiment supprimer {len(files)} fichiers de logs ?"
        )
        if not confirm:
            console.print("Annulé.")
            return

    deleted_count = 0
    for f in files:
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            console.print(f"[red]Erreur lors de la suppression de {f.name}: {e}[/]")

    console.print(f"[green]{deleted_count} fichiers supprimés.[/]")
