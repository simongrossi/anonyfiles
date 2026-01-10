import typer
from pathlib import Path
import yaml
import csv
import json
from multiprocessing import Manager
import concurrent.futures
import os
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.console import Console
from typing import Optional
from typing_extensions import Annotated

try:
    from ..tui.logs_app import LogsApp
except ImportError:
    # This allows the CLI to run even if 'textual' is not installed, as long as the 'interactive' command is not called.
    LogsApp = None

try:
    from anonyfiles_core.anonymizer.engine import AnonyfilesEngine
except ImportError:
    print("Erreur Critique: Impossible d'importer AnonyfilesEngine. Assurez-vous que 'anonyfiles_core' est correctement installé.")
    raise typer.Exit(code=1)

# Crée une nouvelle application Typer pour la sous-commande 'logs'
app = typer.Typer(
    name="logs",
    help="Anonymise des fichiers de log en utilisant des profils spécialisés.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    epilog="""
:sparkles: [bold]Exemples d'utilisation[/bold] :sparkles:

- [bold]Anonymiser un fichier unique avec le profil par défaut ('generic_logs')[/bold]:
  [cyan]$ anonyfiles-cli logs anonymize /var/log/syslog[/cyan]

- [bold]Anonymiser un fichier avec un profil spécifique ('splunk')[/bold]:
  [cyan]$ anonyfiles-cli logs anonymize access.log --profile splunk[/cyan]

- [bold]Anonymiser tous les fichiers '*.log' dans un dossier[/bold]:
  [cyan]$ anonyfiles-cli logs anonymize /path/to/logs/ --profile apache[/cyan]

- [bold]Anonymiser récursivement et spécifier un dossier de sortie[/bold]:
  [cyan]$ anonyfiles-cli logs anonymize /path/to/logs/ -r -o /path/to/output/[/cyan]

- [bold]Lister tous les profils disponibles[/bold]:
  [cyan]$ anonyfiles-cli logs list-profiles[/cyan]

- [bold]Lancer l'interface textuelle interactive (TUI)[/bold]:
  [cyan]$ anonyfiles-cli logs interactive[/cyan]
"""
)

# Définit le chemin vers le dossier des profils de logs à l'intérieur du module CLI
PROFILES_DIR = Path(__file__).parent.parent / "log_profiles"

# --- Fonctions pour le traitement parallèle ---
# Doivent être au niveau supérieur pour être "pickleable" par multiprocessing.

_worker_engine = None

def _init_parallel_worker(config_data: dict, custom_rules: list, shared_mapping_proxy: dict):
    """
    Initialiseur pour chaque processus de travail. Crée une seule instance du moteur par processus.
    """
    global _worker_engine
    try:
        # Chaque processus obtient sa propre instance du moteur, mais ils partagent tous
        # le même dictionnaire de mapping pour une cohérence parfaite.
        _worker_engine = AnonyfilesEngine(
            config=config_data,
            custom_replacement_rules=custom_rules,
            shared_mapping_proxy=shared_mapping_proxy
        )
        # L'état est local à ce processus, mais le mapping est partagé.
        if hasattr(_worker_engine, 'reset_state'):
             _worker_engine.reset_state()
    except Exception as e:
        # Stocke l'exception pour qu'elle soit levée dans le worker.
        _worker_engine = e

def _process_file_parallel(in_file: Path, out_file: Path) -> tuple:
    """
    La tâche exécutée par chaque processus de travail.
    """
    global _worker_engine
    if isinstance(_worker_engine, Exception):
        return "error", in_file, None, f"L'initialisation du worker a échoué: {_worker_engine}"
    if _worker_engine is None:
        return "error", in_file, None, "Le moteur du worker n'a pas été initialisé."

    try:
        # Réinitialise l'état du moteur pour ce fichier spécifique.
        # Cela garantit que le journal d'audit est propre pour chaque fichier.
        if hasattr(_worker_engine, 'reset_state'):
            _worker_engine.reset_state()

        with open(in_file, "r", encoding="utf-8") as f_in, \
             open(out_file, "w", encoding="utf-8") as f_out:
            for line in f_in:
                # Le mapping est mis à jour directement dans le dictionnaire partagé
                # via le shared_mapping_proxy à l'intérieur du moteur.
                anonymized_line, report = _worker_engine.anonymize_text(text=line)
                f_out.write(anonymized_line)
        
        # Récupère le résumé de l'audit pour ce fichier
        audit_summary = _worker_engine.audit_logger.summary()
        return "success", in_file, audit_summary, None
    except Exception as e:
        return "error", in_file, None, str(e)

def _write_global_mapping(output_path: Path, mapping_data: dict):
    """
    Écrit les données de mapping aggrégées dans un fichier CSV.
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["original", "anonymized", "label", "source"])
            # Le mapping de anonymize_text est {original: anonymized}.
            # Le label et la source ne sont pas disponibles dans ce contexte.
            for original, anonymized in mapping_data.items():
                writer.writerow([original, anonymized, "N/A", "log_batch"])
        typer.secho(f"Fichier de mapping global sauvegardé : {output_path}", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Erreur lors de l'écriture du mapping global : {e}", fg=typer.colors.RED)

@app.command(name="list-profiles", help="Affiche la liste de tous les profils de log disponibles.")
def list_log_profiles():
    """
    Scanne le dossier des profils et affiche les profils disponibles.
    """
    console = Console()
    table = Table(title="[bold]Profils de log disponibles[/bold]", show_header=True, header_style="bold magenta", title_style="bold")
    table.add_column("Profil", style="cyan", no_wrap=True, justify="left")
    table.add_column("Description", style="white", justify="left")

    if not PROFILES_DIR.is_dir():
        typer.secho(f"Erreur: Le dossier des profils '{PROFILES_DIR}' est introuvable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    profile_files = sorted(list(PROFILES_DIR.glob("*.yaml")))

    if not profile_files:
        typer.secho("  Aucun profil trouvé.", fg=typer.colors.YELLOW)
        return

    for profile_path in profile_files:
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
                description = config_data.get("description", "[i]Aucune description fournie.[/i]")
            table.add_row(profile_path.stem, description)
        except Exception as e:
            table.add_row(profile_path.stem, f"[bold red]Erreur de lecture du profil: {e}[/bold red]")

    console.print(table)


@app.command(name="interactive", help="Lance l'interface utilisateur textuelle (TUI) pour une utilisation interactive.")
def launch_tui():
    """
    Lance l'application TUI pour l'anonymisation des logs.
    """
    if LogsApp is None:
        typer.secho("Erreur: La dépendance 'textual' est requise pour le mode interactif.", fg=typer.colors.RED)
        typer.secho("Veuillez installer les dépendances de développement via 'make dependencies' ou 'pip install -r requirements-test.txt'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    app_tui = LogsApp()
    app_tui.run()

@app.command(name="anonymize", help="Anonymise un fichier ou un dossier de logs en se basant sur un profil.")
def anonymize_logs_command(
    input_path: Annotated[Path, typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, help="Chemin vers le fichier ou le dossier de logs à anonymiser."
    )],
    profile: Annotated[str, typer.Option(
        "--profile", "-p", help="Nom du profil de log à utiliser (ex: 'splunk', 'apache')."
    )] = "generic_logs",
    output_path: Annotated[Path, typer.Option(
        "--output", "-o", help="Chemin pour le fichier ou dossier de sortie. [défaut: <input>_anonymized...]"
    )] = None,
    pattern: Annotated[str, typer.Option(
        "--pattern", help="Pattern glob pour trouver les fichiers dans un dossier (ex: '*.log')."
    )] = "*.log",
    recursive: Annotated[bool, typer.Option(
        "--recursive", "-r", help="Chercher les fichiers de manière récursive dans les sous-dossiers."
    )] = False,
    global_mapping_path: Annotated[Path, typer.Option(
        "--global-mapping", help="Chemin pour un fichier de mapping CSV global qui agrège tous les remplacements."
    )] = None,
    parallel: Annotated[int, typer.Option(
        "--parallel", help="Nombre de processus à utiliser pour le traitement parallèle (ex: 4). Désactivé par défaut."
    )] = 0,
    audit_logs_dir: Annotated[Path, typer.Option(
        "--audit-logs-dir", help="Dossier pour sauvegarder les rapports d'audit JSON de chaque fichier."
    )] = None,
):
    """
    Commande CLI pour anonymiser un fichier ou un dossier de logs.
    """
    # 1. Load config and instantiate engine ONCE
    config_path = PROFILES_DIR / f"{profile}.yaml"
    if not config_path.is_file():
        typer.secho(f"Erreur: Le profil de configuration '{profile}' est introuvable.", fg=typer.colors.RED)
        typer.secho(f"Le fichier '{config_path}' n'existe pas.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Chargement du moteur Anonyfiles avec le profil : {config_path}...")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        custom_rules = config_data.get("custom_rules", [])

    except Exception as e:
        typer.secho(f"\nErreur lors de l'initialisation du moteur d'anonymisation : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 2. Determine list of files to process
    files_to_process = []
    if input_path.is_file():
        files_to_process.append(input_path)
    elif input_path.is_dir():
        if output_path and output_path.is_file():
            typer.secho("Erreur: Si l'entrée est un dossier, la sortie (--output) doit aussi être un dossier, pas un fichier.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        glob_method = input_path.rglob if recursive else input_path.glob
        files_to_process = sorted(list(glob_method(pattern)))

    if not files_to_process:
        typer.secho(f"Aucun fichier à traiter trouvé pour le chemin '{input_path}' et le pattern '{pattern}'.", fg=typer.colors.YELLOW)
        raise typer.Exit()

    # 3. Choisir le chemin d'exécution: séquentiel ou parallèle
    if parallel > 0:
        _run_parallel(parallel, files_to_process, input_path, output_path, config_data, custom_rules, global_mapping_path, audit_logs_dir)
    else:
        if custom_rules:
            typer.echo(f"  - {len(custom_rules)} règle(s) personnalisée(s) chargée(s) depuis le profil.")
        engine = AnonyfilesEngine(
            config=config_data, custom_replacement_rules=custom_rules
        )
        _run_sequential(engine, files_to_process, input_path, output_path, global_mapping_path)

def _run_sequential(engine: AnonyfilesEngine, files_to_process: list, input_path: Path, output_path: Optional[Path], global_mapping_path: Optional[Path]):
    """Exécute le traitement de manière séquentielle."""
    typer.echo(f"\nLancement du traitement séquentiel pour {len(files_to_process)} fichier(s)...")
    global_mapping = {}
    success_count = 0
    error_count = 0

    if hasattr(engine, 'reset_state'):
        engine.reset_state()

    with typer.progressbar(files_to_process, label="Traitement des fichiers") as progress:
        for in_file in progress:
            if input_path.is_file():
                if output_path and output_path.is_dir():
                    out_file = output_path / in_file.name
                else:
                    out_file = output_path or in_file.with_name(f"{in_file.stem}_anonymized{in_file.suffix}")
            else:
                output_dir = output_path or input_path.parent / f"{input_path.name}_anonymized"
                relative_path = in_file.relative_to(input_path)
                out_file = output_dir / relative_path
            out_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(in_file, "r", encoding="utf-8") as f_in, \
                     open(out_file, "w", encoding="utf-8") as f_out:
                    for line in f_in:
                        anonymized_line, report = engine.anonymize_text(text=line)
                        f_out.write(anonymized_line)
                        if global_mapping_path and "mapping" in report:
                            global_mapping.update(report["mapping"])
                success_count += 1
            except Exception as e:
                typer.secho(f"\nErreur lors du traitement de {in_file.name}: {e}", fg=typer.colors.RED, err=True)
                error_count += 1

    if global_mapping_path and global_mapping:
        _write_global_mapping(global_mapping_path, global_mapping)

    typer.echo("\n--- Rapport de traitement ---")
    typer.secho(f"Fichiers traités avec succès : {success_count}", fg=typer.colors.GREEN)
    if error_count > 0:
        typer.secho(f"Fichiers en erreur : {error_count}", fg=typer.colors.RED)
    typer.echo("--------------------------")

def _run_parallel(num_workers: int, files_to_process: list, input_path: Path, output_path: Optional[Path], config_data: dict, custom_rules: list, global_mapping_path: Optional[Path], audit_logs_dir: Optional[Path]):
    """Exécute le traitement en parallèle."""
    typer.echo(f"\nLancement du traitement parallèle avec {num_workers} processus pour {len(files_to_process)} fichier(s)...")

    if audit_logs_dir:
        audit_logs_dir.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Les rapports d'audit seront sauvegardés dans : {audit_logs_dir}")

    success_count = 0
    error_count = 0

    # Préparer les arguments pour chaque tâche
    tasks = []
    for in_file in files_to_process:
        if input_path.is_file():
            if output_path and output_path.is_dir():
                out_file = output_path / in_file.name
            else:
                out_file = output_path or in_file.with_name(f"{in_file.stem}_anonymized{in_file.suffix}")
        else:
            output_dir = output_path or input_path.parent / f"{input_path.name}_anonymized"
            relative_path = in_file.relative_to(input_path)
            out_file = output_dir / relative_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        tasks.append((in_file, out_file))

    with Manager() as manager:
        # Ce dictionnaire est partagé entre tous les processus de travail.
        shared_mapping = manager.dict()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            task_id = progress.add_task("Traitement des fichiers...", total=len(tasks))

            init_args = (config_data, custom_rules, shared_mapping)
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers, initializer=_init_parallel_worker, initargs=init_args) as executor:
                futures = [executor.submit(_process_file_parallel, in_f, out_f) for in_f, out_f in tasks]

                for future in concurrent.futures.as_completed(futures):
                    status, file_path, audit_summary, error_msg = future.result()
                    if status == "success":
                        success_count += 1
                        # Sauvegarde du rapport d'audit si demandé
                        if audit_logs_dir and audit_summary:
                            audit_file_path = audit_logs_dir / f"{file_path.stem}_audit.json"
                            try:
                                with open(audit_file_path, "w", encoding="utf-8") as f_audit:
                                    json.dump(audit_summary, f_audit, indent=2, ensure_ascii=False)
                            except Exception as e:
                                typer.secho(f"\nErreur lors de la sauvegarde du rapport d'audit pour {file_path.name}: {e}", fg=typer.colors.RED, err=True)
                    else:
                        error_count += 1
                        typer.secho(f"\nErreur lors du traitement de {file_path.name}: {error_msg}", fg=typer.colors.RED, err=True)
                    progress.update(task_id, advance=1)

        # Une fois tous les processus terminés, on écrit le mapping global cohérent.
        if global_mapping_path and shared_mapping:
            _write_global_mapping(global_mapping_path, dict(shared_mapping))

    typer.echo("\n--- Rapport de traitement ---")
    typer.secho(f"Fichiers traités avec succès : {success_count}", fg=typer.colors.GREEN)
    if error_count > 0:
        typer.secho(f"Fichiers en erreur : {error_count}", fg=typer.colors.RED)
    typer.echo("--------------------------")