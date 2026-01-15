
import logging
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from anonyfiles_cli.managers.config_manager import ConfigManager
from anonyfiles_cli.utils.default_paths import get_default_log_dir

# Initialisation du logger et de la console
logger = logging.getLogger(__name__)
console = Console()

# Définition de l'application Typer
app = typer.Typer(help="Gestion et analyse des fichiers de logs.")


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
    except ImportError as e:
        console.print("[bold red]Erreur:[/bold red] Textual n'est pas installé. Veuillez l'installer avec :")
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
def clear_logs(force: bool = typer.Option(False, "--force", "-f", help="Forcer la suppression sans confirmation")):
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
        confirm = typer.confirm(f"Voulez-vous vraiment supprimer {len(files)} fichiers de logs ?")
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
