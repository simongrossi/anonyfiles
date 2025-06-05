# anonyfiles_cli/handlers/deanonymize_handler.py

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import typer # Importez typer si vous comptez l'utiliser pour les messages ou confirmations

from ..anonymizer.deanonymize import Deanonymizer
from ..anonymizer.file_utils import timestamp
from ..anonymizer.run_logger import log_run_event
from ..ui.console_display import ConsoleDisplay
from ..cli_logger import CLIUsageLogger
from ..exceptions import AnonyfilesError


class DeanonymizeHandler:
    def __init__(self, console: ConsoleDisplay):
        self.console = console

    def process(self,
                input_file: Path,
                mapping_csv: Path,
                output: Optional[Path],
                report: Optional[Path],
                dry_run: bool,
                permissive: bool):
        """
        Traite la désanonymisation d'un fichier en orchestrant les différentes étapes.
        """
        run_id = timestamp() # Générez le run_id ici pour la désanonymisation aussi
        self.console.console.print(f"🔁 Désanonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]")
        self.console.console.print(f"🔗 Fichier de mapping : [bold green]{mapping_csv}[/bold green]")

        strict_mode = not permissive
        
        try:
            output_path = output
            if not output_path and not dry_run:
                # Assurez-vous que le run_id est utilisé pour le nommage si on le génère
                output_path = input_file.parent / f"{input_file.stem}_deanonymise_{run_id}{input_file.suffix}"
                
            report_path = report
            if not report_path and not dry_run and output_path:
                report_path = output_path.parent / f"{input_file.stem}_deanonymise_report_{run_id}.json"

            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if output_path.exists() and not typer.confirm(f"⚠️ Le fichier de sortie '{output_path}' existe déjà. L'écraser ?"):
                    return False # Indique l'échec (annulation par l'utilisateur)

            with open(input_file, encoding="utf-8") as f:
                content = f.read()

            deanonymizer = Deanonymizer(str(mapping_csv), strict=not permissive)

            # Si le chargement du mapping a des erreurs critiques qui empêchent la désanonymisation
            if deanonymizer.map_loading_warnings and not deanonymizer.code_to_originals:
                warning_message = f"Échec critique du chargement du fichier mapping '{mapping_csv}'. Avertissements: {deanonymizer.map_loading_warnings}"
                self.console.console.print(f"❌ {warning_message}", style="red")
                # Log l'événement d'erreur ici si le processus ne peut pas continuer
                log_run_event(
                    logger=CLIUsageLogger,
                    run_id=run_id,
                    input_file=str(input_file),
                    output_file="N/A",
                    mapping_file=str(mapping_csv),
                    log_entities_file="",
                    entities_detected=[],
                    total_replacements=0,
                    audit_log=[warning_message],
                    status="error",
                    error=warning_message
                )
                return False

            restored_text, report_data = deanonymizer.deanonymize_text(content, dry_run=dry_run)

            if not dry_run:
                if output_path:
                    output_path.write_text(restored_text, encoding="utf-8")
                    self.console.console.print(f"✅ Fichier restauré avec succès : [bold green]{output_path}[/bold green]")
                else:
                    self.console.console.print("INFO: Mode non-dry_run mais aucun fichier de sortie (--output) spécifié. Texte restauré non sauvegardé.")
                    self.console.console.print("\n--- Texte restauré (aperçu, max 1000 caractères) ---")
                    self.console.console.print(restored_text[:1000] + ("..." if len(restored_text) > 1000 else ""), style="dim")
                    self.console.console.print("---------------------------------------------------")

                if report_path:
                    report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
                    self.console.console.print(f"📊 Rapport de désanonymisation détaillé sauvegardé : [bold green]{report_path}[/bold green]")
                elif not output_path:
                    self.console.console.print("\n--- Rapport de désanonymisation (JSON) ---")
                    self.console.console.print(json.dumps(report_data, indent=2, ensure_ascii=False), style="dim")
                    self.console.console.print("----------------------------------------")
                
                self.console.console.print("✅ Désanonymisation terminée.")

            else:
                self.console.console.print(typer.rich_utils.make_panel(
                    f"[bold yellow]Simulation de désanonymisation (dry_run) terminée.[/bold yellow]\n"
                    f"Fichier d'entrée analysé : [green]{input_file}[/green]\n"
                    f"Fichier de mapping utilisé : [green]{mapping_csv}[/green]\n"
                    f"Mode strict : [yellow]{strict_mode}[/yellow] (permissif : [yellow]{permissive}[/yellow])",
                    border_style="yellow"
                ))
                self.console.console.print(f"Nombre de codes remplacés (estimé) : [bold]{report_data.get('replacements_successful_count', 'N/A')}[/bold]")
                self.console.console.print(f"Couverture du mapping (estimé) : [bold]{report_data.get('coverage_percentage', 'N/A')}[/bold]")
                if report_data.get('warnings_generated_during_deanonymization'):
                    self.console.console.print("⚠️ Avertissements générés pendant la simulation :")
                    for warning_msg in report_data['warnings_generated_during_deanonymization']:
                        self.console.console.print(f"  - [yellow]{warning_msg}[/yellow]")
                self.console.console.print("Aucun fichier n'a été écrit.")
            
            log_run_event(
                logger=CLIUsageLogger,
                run_id=run_id, # Utilisez l'ID généré au début
                input_file=str(input_file),
                output_file=str(output_path) if output_path and not dry_run else "DRY_RUN_NO_OUTPUT",
                mapping_file=str(mapping_csv),
                log_entities_file="",
                entities_detected=report_data.get("distinct_codes_in_text_list", []),
                total_replacements=report_data.get("replacements_successful_count", 0),
                audit_log=report_data.get("warnings_generated_during_deanonymization", []),
                status="success" if not report_data.get("warnings_generated_during_deanonymization") else "success_with_warnings",
                error=None
            )
            # AJOUTEZ CETTE LIGNE POUR AFFICHER L'ID DU JOB
            if not dry_run and output_path:
                actual_base_path = output_path.parent.resolve()
                self.console.console.print(f"\n✨ Job ID : [bold green]{run_id}[/bold green] (utilisez 'anonyfiles_cli job delete {run_id} --output-dir {actual_base_path}' pour supprimer les fichiers)")
            return True # Indique le succès

        except AnonyfilesError as e:
            self.console.handle_error(e, "deanonymization_process")
            return False # Indique l'échec
        except Exception as e:
            self.console.handle_error(e, "deanonymization_process_unexpected")
            return False # Indique l'échec
