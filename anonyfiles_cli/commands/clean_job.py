# anonyfiles_cli/commands/clean_job.py

import typer
from pathlib import Path
import shutil

# Importations des modules nécessaires
from anonyfiles_cli.managers.config_manager import ConfigManager
from anonyfiles_cli.ui.console_display import ConsoleDisplay
from anonyfiles_cli.exceptions import AnonyfilesError
from anonyfiles_cli.utils.default_paths import get_default_output_dir

app = typer.Typer(help="Commandes pour gérer et nettoyer les jobs.")
console = ConsoleDisplay()

@app.command(name="delete", help="Supprime un répertoire de job et tous ses fichiers (anonymisés, mapping, logs).")
def delete_job(
    job_id: str = typer.Argument(..., help="ID du job à supprimer (ex: un timestamp comme 20250605-123456)."),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Répertoire principal des sorties Anonyfiles si différent de la valeur par défaut configurée."
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Supprime sans confirmation.")
):
    """
    Supprime le répertoire complet d'un job d'anonymisation/désanonymisation.
    """
    try:
        # Récupérer le répertoire de sortie par défaut à partir de la configuration si non fourni
        if output_dir is None:
            effective_config = ConfigManager.get_effective_config(None)
            # Assurez-vous que le default_output_dir est bien une chaîne ou un Path
            default_configured_output_dir = effective_config.get("default_output_dir", None)
            if default_configured_output_dir:
                output_dir = Path(default_configured_output_dir)
            else:
                # Fallback si non configuré ou absent
                output_dir = get_default_output_dir()
        
        # Le répertoire où les jobs sont stockés (jobs/run_id)
        # Selon file_utils.py, c'est `base_output_dir / "runs" / run_id`
        runs_base_dir = output_dir / "runs"
        
        target_job_dir = runs_base_dir / job_id

        console.console.print(f"🗑️ Tentative de suppression du job : [bold cyan]{job_id}[/bold cyan]")
        console.console.print(f"📁 Chemin : [dim]{target_job_dir}[/dim]")

        if not target_job_dir.is_dir():
            console.console.print(f"❌ Erreur : Le répertoire du job '{job_id}' est introuvable à '{target_job_dir}'.", style="red")
            raise typer.Exit(1)

        if not force and not typer.confirm(f"⚠️ Êtes-vous sûr de vouloir supprimer définitivement le job '{job_id}' et tout son contenu ({target_job_dir}) ? Cette action est irréversible."):
            console.console.print("Opération de suppression annulée par l'utilisateur.", style="yellow")
            raise typer.Exit()
        
        shutil.rmtree(target_job_dir)
        console.console.print(f"✅ Le job '{job_id}' a été supprimé avec succès.", style="green")

    except AnonyfilesError as e:
        console.handle_error(e, "delete_job_command")
        raise typer.Exit(e.exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        console.handle_error(e, "delete_job_command_unexpected")
        raise typer.Exit(1)

@app.command(name="list", help="Liste tous les jobs disponibles dans le répertoire de sortie.")
def list_jobs(
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Répertoire principal des sorties Anonyfiles si différent de la valeur par défaut configurée."
    )
):
    """
    Liste tous les répertoires de jobs (timestamps) trouvés dans le dossier `runs`.
    """
    try:
        if output_dir is None:
            effective_config = ConfigManager.get_effective_config(None)
            default_configured_output_dir = effective_config.get("default_output_dir", None)
            if default_configured_output_dir:
                output_dir = Path(default_configured_output_dir)
            else:
                output_dir = get_default_output_dir()
        
        runs_base_dir = output_dir / "runs"

        console.console.print(f"📁 Listing des jobs dans : [bold blue]{runs_base_dir}[/bold blue]")

        if not runs_base_dir.is_dir():
            console.console.print(f"ℹ️ Le répertoire des jobs '{runs_base_dir}' n'existe pas.", style="dim")
            raise typer.Exit()

        job_folders = [f.name for f in runs_base_dir.iterdir() if f.is_dir()]
        
        if not job_folders:
            console.console.print("Pas de jobs trouvés.", style="dim")
            return

        for job_id in sorted(job_folders):
            console.console.print(f"  - [cyan]{job_id}[/cyan]")
        
    except AnonyfilesError as e:
        console.handle_error(e, "list_jobs_command")
        raise typer.Exit(e.exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        console.handle_error(e, "list_jobs_command_unexpected")
        raise typer.Exit(1)
