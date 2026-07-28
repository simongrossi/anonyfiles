# anonyfiles_cli/ui/console_display.py

import contextlib
import traceback
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..exceptions import (
    AnonyfilesError,
    ConfigurationError,
    FileIOError,
    ProcessingError,
)


class ConsoleDisplay:
    def __init__(self):
        self.console = Console()

    def display_welcome(self):
        """Affiche le message de bienvenue de l'application."""
        self.console.print(
            Panel.fit(
                "[bold blue]🕵️‍♂️ Anonyfiles CLI[/bold blue]\n"
                "Anonymisation intelligente de documents",
                border_style="blue",
            )
        )
        self.console.print("")

    def display_results(
        self, result: dict[str, Any], dry_run: bool, paths: dict[str, Path]
    ):
        """
        Affiche un résumé des résultats de l'anonymisation.
        :param result: Dictionnaire des résultats de l'engine d'anonymisation.
        :param dry_run: Indique si c'était un dry-run.
        :param paths: Dictionnaire des chemins de fichiers de sortie.
        """
        if dry_run:
            self.console.print(
                "🔍 [yellow]Mode simulation - Aucun fichier modifié[/yellow]"
            )
        else:
            self.console.print("✅ [green]Anonymisation terminée avec succès![/green]")

        table = Table(title="Résultats de l'Anonymisation")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")

        table.add_row(
            "Entités détectées (spaCy)", str(len(result.get("entities_detected", [])))
        )
        table.add_row(
            "Remplacements totaux (custom + spaCy)",
            str(result.get("total_replacements", 0)),
        )

        if not dry_run:
            if paths.get("output_file") and paths["output_file"].exists():
                table.add_row("Fichier anonymisé", str(paths["output_file"]))
            if paths.get("mapping_file") and paths["mapping_file"].exists():
                table.add_row("Mapping CSV", str(paths["mapping_file"]))
            if paths.get("log_entities_file") and paths["log_entities_file"].exists():
                table.add_row("Log des entités", str(paths["log_entities_file"]))
            if paths.get("bundle_file") and paths["bundle_file"].exists():
                table.add_row("Bundle", str(paths["bundle_file"]))

        self.console.print(table)

        if result.get("audit_log"):
            self.console.print(
                "\n📊 [bold blue]Journal d'Audit des Remplacements :[/bold blue]"
            )
            audit_table = Table(show_header=True, header_style="bold magenta")
            audit_table.add_column("Original", style="white")
            audit_table.add_column("Remplacement", style="green")
            audit_table.add_column("Type", style="cyan")
            audit_table.add_column("Count", style="yellow", justify="right")
            for entry in result["audit_log"]:
                original = str(entry.get("pattern", "N/A"))
                replacement = str(entry.get("replacement", "N/A"))
                type_val = str(entry.get("type", "N/A"))
                count = str(entry.get("count", 0))
                audit_table.add_row(original, replacement, type_val, count)
            self.console.print(audit_table)

        self.console.print("")

    def handle_error(self, error: Exception, context: str = ""):
        """
        Gestionnaire d'erreurs centralisé avec affichage Rich.
        :param error: L'exception levée.
        :param context: Contexte de l'erreur (où elle s'est produite).
        """
        from ..cli_logger import CLIUsageLogger

        command_name = None
        params = None
        with contextlib.suppress(Exception):
            ctx = typer.get_current_context()
            command_name = ctx.command_path
            params = ctx.params

        if isinstance(error, ConfigurationError):
            if "spaCy model" in str(error) and "Install manualy" in str(error):
                # Message spécifique et visible pour l'erreur de modèle manquant
                title = "❌ Modèle spaCy manquant ou inaccessible"
                msg = (
                    "Le modèle linguistique nécessaire n'a pas pu être chargé.\n\n"
                    "Veuillez exécuter la commande suivante pour l'installer :\n"
                    "[bold green]python -m spacy download fr_core_news_md[/bold green]"
                )
                self.console.print(Panel(msg, title=title, border_style="red"))
            else:
                self.console.print(
                    f"⚙️  [yellow]Erreur de configuration:[/yellow] {error}"
                )

            CLIUsageLogger.log_error(context, error, command=command_name, args=params)
        elif isinstance(error, FileIOError):
            self.console.print(f"📂 [red]Erreur fichier:[/red] {error}")
            CLIUsageLogger.log_error(context, error, command=command_name, args=params)
        elif isinstance(error, ProcessingError):
            self.console.print(f"⚠️  [red]Erreur de traitement:[/red] {error}")
            CLIUsageLogger.log_error(context, error, command=command_name, args=params)
        elif isinstance(error, AnonyfilesError):
            self.console.print(f"❌ [red]Erreur :[/red] {error}")
            CLIUsageLogger.log_error(context, error, command=command_name, args=params)
        else:
            self.console.print(f"❌ [red]Erreur inattendue:[/red] {error}")
            self.console.print(f"[red]Contexte de l'erreur: {context}[/red]")
            CLIUsageLogger.log_error(
                f"{context}_unexpected_error",
                error,
                command=command_name,
                args=params,
            )
            self.console.print("[red]Veuillez signaler ce bug si cela persiste.[/red]")
            self.console.print(traceback.format_exc(), style="dim red")
