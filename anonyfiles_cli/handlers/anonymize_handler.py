# anonyfiles_cli/handlers/anonymize_handler.py

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import typer # Importez typer si vous comptez l'utiliser pour les messages ou confirmations

from anonyfiles_core import AnonyfilesEngine
from anonyfiles_core.anonymizer.run_logger import log_run_event
from anonyfiles_core.anonymizer.file_utils import (
    timestamp,
    default_output,
    default_mapping,
    default_log,
)
from ..managers.path_manager import PathManager
from ..managers.config_manager import ConfigManager
from ..managers.validation_manager import ValidationManager
from ..ui.console_display import ConsoleDisplay
from ..cli_logger import CLIUsageLogger
from ..exceptions import (
    AnonyfilesError,
    ConfigurationError,
    FileIOError,
    ProcessingError,
)


class AnonymizeHandler:
    def __init__(self, console: ConsoleDisplay):
        self.console = console

    def process(self,
                input_file: Path,
                config_path: Optional[Path],
                output: Optional[Path],
                log_entities: Optional[Path],
                mapping_output: Optional[Path],
                bundle_output: Optional[Path],
                output_dir: Path,
                dry_run: bool,
                csv_no_header: bool, # Reçoit l'option directe
                has_header_opt: Optional[str], # Reçoit l'option directe
                exclude_entities: Optional[List[str]],
                custom_replacements_json: Optional[str],
                append_timestamp: bool,
                force: bool):
        """
        Traite l'anonymisation d'un fichier en orchestrant les différentes étapes.
        """
        run_id = timestamp()
        self.console.console.print(f"📂 Anonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]")

        csv_has_header_bool: Optional[bool] = None
        if has_header_opt is not None:
            csv_has_header_bool = has_header_opt.lower() == "true"
        else:
            csv_has_header_bool = not csv_no_header # Si has_header_opt non défini, utilise csv_no_header

        try:
            # 1. Configuration
            effective_config = ConfigManager.get_effective_config(config_path)
            self.console.console.print("🔧 Configuration chargée et validée.")

            # 2. Résolution des chemins
            path_manager = PathManager(input_file, output_dir, run_id, append_timestamp)
            paths = path_manager.resolve_paths(output, mapping_output, log_entities, dry_run, bundle_output)
            self.console.console.print("➡️  Chemins de sortie résolus.")

            # 3. Vérifications pré-traitement (écrasement de fichiers)
            if not dry_run:
                ValidationManager.check_overwrite(
                    [
                        p
                        for p in paths.values()
                        if p.name
                        not in [
                            "dry_run_output.tmp",
                            "dry_run_mapping.tmp",
                            "dry_run_log.tmp",
                            "dry_run_bundle.tmp",
                        ]
                    ],
                    force,
                )
            
            self.console.console.print("⚙️  Démarrage du traitement d'anonymisation...")

            # 4. Préparation et exécution du moteur AnonyfilesEngine
            custom_rules_list = ValidationManager.parse_custom_replacements(custom_replacements_json)

            engine = AnonyfilesEngine(
                config=effective_config,
                exclude_entities_cli=exclude_entities,
                custom_replacement_rules=custom_rules_list
            )

            processor_kwargs = {}
            if input_file.suffix.lower() == ".csv" and csv_has_header_bool is not None:
                processor_kwargs['has_header'] = csv_has_header_bool

            result = engine.anonymize(
                input_path=input_file,
                output_path=paths.get("output_file"),
                entities=None, # La gestion des entités exclues est dans AnonyfilesEngine
                dry_run=dry_run,
                log_entities_path=paths.get("log_entities_file"),
                mapping_output_path=paths.get("mapping_file"),
                **processor_kwargs
            )

            if result.get("status") == "error":
                raise ProcessingError(result.get('error', 'Le moteur d\'anonymisation a signalé une erreur.'))
            
            # 5. Affichage et logging
            self.console.display_results(result, dry_run, paths)

            log_run_event(
                logger=CLIUsageLogger,
                run_id=run_id,
                input_file=str(input_file),
                output_file=str(paths.get("output_file")) if paths.get("output_file") and not dry_run else "DRY_RUN_NO_OUTPUT",
                mapping_file=str(paths.get("mapping_file")) if paths.get("mapping_file") and not dry_run else "DRY_RUN_NO_MAPPING",
                log_entities_file=str(paths.get("log_entities_file")) if paths.get("log_entities_file") and not dry_run else "DRY_RUN_NO_LOG",
                entities_detected=result.get("entities_detected", []),
                total_replacements=result.get("total_replacements", 0),
                audit_log=result.get("audit_log", []),
                status=result.get("status", "unknown"),
                error=result.get("error")
            )
            if not dry_run and bundle_output:
                from anonyfiles_core.anonymizer.bundle_handler import create_bundle
                create_bundle(
                    paths.get("bundle_file"),
                    paths.get("output_file"),
                    paths.get("mapping_file"),
                    result.get("audit_log", []),
                    paths.get("log_entities_file"),
                )
                self.console.console.print(
                    f"🎁 Bundle créé : [bold green]{paths.get('bundle_file')}[/bold green]"
                )
            # AJOUTEZ CETTE LIGNE POUR AFFICHER L'ID DU JOB
            if not dry_run and paths.get("output_file"):
                full_output_base_path = path_manager.base_output_dir.resolve()
                self.console.console.print(f"\n✨ Job ID : [bold green]{run_id}[/bold green] (utilisez 'anonyfiles_cli job delete {run_id} --output-dir {full_output_base_path}' pour supprimer les fichiers)")
            return True # Indique le succès

        except (ConfigurationError, FileIOError, ProcessingError) as e:
            self.console.handle_error(e, "anonymization_process")
            return False  # Indique l'échec
        except AnonyfilesError as e:
            self.console.handle_error(e, "anonymization_process")
            return False  # Indique l'échec
        except Exception as e:
            self.console.handle_error(e, "anonymization_process_unexpected")
            return False  # Indique l'échec
