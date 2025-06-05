# anonyfiles_cli/handlers/batch_handler.py

from pathlib import Path
from typing import List, Dict, Any, Optional
import typer

from ..handlers.anonymize_handler import AnonymizeHandler
from ..managers.config_manager import ConfigManager
from ..ui.console_display import ConsoleDisplay
from ..exceptions import AnonyfilesError, ProcessingError

class BatchHandler:
    def __init__(self, console: ConsoleDisplay):
        self.console = console
        self.supported_extensions = {'.txt', '.csv', '.json', '.docx', '.xlsx', '.pdf'}

    def process_directory(self,
                          input_dir: Path,
                          pattern: str,
                          output_dir: Optional[Path],
                          config: Optional[Path],
                          dry_run: bool,
                          recursive: bool,
                          # Passer les options CSV si le batch doit les gérer uniformément
                          csv_no_header: bool,
                          has_header_opt: Optional[str]):
        """
        Traite un répertoire de fichiers en lot.
        """
        if not input_dir.exists() or not input_dir.is_dir():
            self.console.console.print("❌ Le dossier d'entrée n'existe pas", style="red")
            raise AnonyfilesError("Le dossier d'entrée n'existe pas ou n'est pas un répertoire.")
        
        files = self._find_files(input_dir, pattern, recursive)
        
        if not files:
            self.console.console.print(f"❌ Aucun fichier trouvé avec le pattern '[yellow]{pattern}[/yellow]' dans '[cyan]{input_dir}[/cyan]'")
            return
        
        self.console.console.print(f"🔄 [bold]{len(files)} fichiers trouvés pour le traitement batch.[/bold]")
        
        if not dry_run and not typer.confirm(f"Traiter {len(files)} fichiers ?"):
            raise AnonyfilesError("Opération annulée par l'utilisateur.")
        
        if not output_dir:
            output_dir = input_dir / "anonymized_output"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        error_count = 0
        
        anonymize_handler = AnonymizeHandler(self.console) # Utilise la même instance de console

        for i, file_path in enumerate(files, 1):
            self.console.console.print(f"[{i}/{len(files)}] 📄 [blue]{file_path.name}[/blue]...")
            
            try:
                # Génération des chemins de sortie pour chaque fichier du batch
                # Les chemins par défaut sont générés dans un sous-dossier de output_dir
                # Recrée le run_id pour chaque fichier afin d'avoir des dossiers de run séparés.
                # Ou si on veut tout dans un seul dossier de run, il faut générer un run_id global au batch.
                # Pour la simplicité, on va les mettre directement dans output_dir sans sous-dossier de run_id.
                
                # Le PathManager est conçu pour créer des run_dirs. Pour le batch, on peut contourner ou l'adapter.
                # Ici, je vais simplifier pour que les fichiers soient directement dans output_dir.
                
                relative_path = file_path.relative_to(input_dir)
                current_output_file = output_dir / relative_path
                current_output_file.parent.mkdir(parents=True, exist_ok=True)

                # Les chemins log et mapping sont optionnels, générés à côté de l'output
                current_log_entities_file = current_output_file.parent / f"{current_output_file.stem}_entities.csv"
                current_mapping_file = current_output_file.parent / f"{current_output_file.stem}_mapping.csv"

                # Pour le batch, on ne veut pas forcément des timestamps sur chaque fichier.
                # Par défaut, append_timestamp=False pour un output plus propre dans un dossier batch.
                # L'utilisateur peut ajouter une option --append-timestamp-batch si besoin.
                
                # On utilise la méthode process de AnonymizeHandler
                success = anonymize_handler.process(
                    input_file=file_path,
                    config_path=config,
                    output=current_output_file, # Chemin de sortie spécifique au fichier
                    log_entities=current_log_entities_file,
                    mapping_output=current_mapping_file,
                    output_dir=output_dir, # Le output_dir de base du batch
                    dry_run=dry_run,
                    csv_no_header=csv_no_header,
                    has_header_opt=has_header_opt,
                    exclude_entities=None, # Les exclusions sont gérées par la config ou passées au handler
                    custom_replacements_json=None, # Les règles custom sont gérées par la config ou passées au handler
                    append_timestamp=False, # Pour un output plus propre dans le batch
                    force=True # En mode batch, on suppose qu'on écrase
                )
                
                if success:
                    success_count += 1
                    self.console.console.print(f"  ✅ Traité avec succès -> [green]{current_output_file.relative_to(output_dir.parent)}[/green]", style="green")
                else:
                    error_count += 1
                    # Le message d'erreur est déjà géré par l'AnonymizeHandler
                    self.console.console.print(f"  ❌ Échec du traitement de [red]{file_path.name}[/red]", style="red")
                    
            except Exception as e:
                error_count += 1
                self.console.console.print(f"  ❌ Erreur inattendue : [red]{e}[/red] sur [red]{file_path.name}[/red]", style="red")
        
        self.console.console.print(f"\n📊 [bold]Résumé du traitement batch:[/bold]")
        self.console.console.print(f"✅ Succès : [green]{success_count}[/green]")
        self.console.console.print(f"❌ Erreurs : [red]{error_count}[/red]")
        self.console.console.print(f"📁 Dossier de sortie : [blue]{output_dir}[/blue]")

    def _find_files(self, input_dir: Path, pattern: str, recursive: bool) -> List[Path]:
        """
        Trouve les fichiers à traiter dans le répertoire donné, en appliquant le pattern
        et l'option récursive.
        """
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))
        
        return [f for f in files if f.suffix.lower() in self.supported_extensions and f.is_file()]