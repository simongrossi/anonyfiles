# anonyfiles_cli/handlers/validation_handler.py

import json
from pathlib import Path
from typing import Optional, List
import typer # Importez typer si nécessaire pour les exceptions ou messages

from ..exceptions import ConfigurationError # Assurez-vous que cette exception est définie

class ValidationHandler:
    SUPPORTED_EXTENSIONS = {".txt", ".csv", ".docx", ".xlsx", ".pdf", ".json"}
    
    @classmethod
    def validate_anonymize_inputs(cls,
                                  input_file: Path,
                                  output: Optional[Path], # Non utilisé pour la validation d'extension, mais peut être utile si on valide le chemin de sortie
                                  custom_replacements_json: Optional[str],
                                  csv_no_header: bool,
                                  has_header_opt: Optional[str]):
        """Validate inputs for anonymization.

        Args:
            input_file (Path): File provided to the command.
            output (Optional[Path]): Optional destination file for anonymized output.
            custom_replacements_json (Optional[str]): JSON string containing custom replacement rules.
            csv_no_header (bool): Indicates CSV input has no header row.
            has_header_opt (Optional[str]): Explicit CSV header flag ("true"/"false").

        Raises:
            ConfigurationError: If an option is invalid or files are missing.
        """
        cls._validate_file_extension(input_file)
        cls._validate_csv_options(input_file, csv_no_header, has_header_opt)
        cls._validate_custom_replacements(custom_replacements_json)
    
    @classmethod
    def validate_deanonymize_inputs(cls,
                                    input_file: Path,
                                    mapping_csv: Path):
        """Validate inputs for deanonymization.

        Args:
            input_file (Path): Anonymized file to restore.
            mapping_csv (Path): Mapping file generated during anonymization.

        Raises:
            ConfigurationError: If the files are missing or invalid.
        """
        if not input_file.exists() or not input_file.is_file():
            raise ConfigurationError(f"Le fichier d'entrée '{input_file}' est introuvable ou n'est pas un fichier.")
        if not mapping_csv.exists() or not mapping_csv.is_file():
            raise ConfigurationError(f"Le fichier de mapping '{mapping_csv}' est introuvable ou n'est pas un fichier.")
        if mapping_csv.suffix.lower() != ".csv":
            raise ConfigurationError(f"Le fichier de mapping doit être un fichier CSV (.csv), mais a l'extension : {mapping_csv.suffix}")


    @classmethod
    def _validate_file_extension(cls, file_path: Path):
        """Valide l'extension d'un fichier."""
        if file_path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ConfigurationError(f"Extension de fichier non supportée : {file_path.suffix}. Extensions supportées : {', '.join(cls.SUPPORTED_EXTENSIONS)}")
    
    @classmethod
    def _validate_csv_options(cls, input_file: Path, csv_no_header: bool,
                             has_header_opt: Optional[str]):
        """Valide la cohérence des options CSV avec le type de fichier."""
        if csv_no_header and input_file.suffix.lower() != ".csv":
            raise ConfigurationError("--csv-no-header ne peut être utilisé que pour les fichiers CSV.")
        
        if has_header_opt and has_header_opt.lower() not in ("true", "false"):
            raise ConfigurationError("--has-header-opt doit être 'true' ou 'false'.")
    
    @classmethod  
    def _validate_custom_replacements(cls, custom_replacements_json: Optional[str]):
        """Valide le format JSON des règles de remplacement personnalisées."""
        if custom_replacements_json:
            try:
                parsed = json.loads(custom_replacements_json)
                if not isinstance(parsed, list):
                    raise ConfigurationError("Les règles de remplacement personnalisées doivent être une liste JSON.")
                for i, rule in enumerate(parsed):
                    if not isinstance(rule, dict) or "pattern" not in rule or "replacement" not in rule:
                        raise ConfigurationError(f"Règle personnalisée invalide à l'index {i}. Chaque règle doit être un objet JSON avec 'pattern' et 'replacement'.")
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Format JSON invalide pour les règles de remplacement personnalisées : {e}.")
            except Exception as e:
                raise ConfigurationError(f"Erreur inattendue lors de la validation des règles personnalisées : {e}.")
