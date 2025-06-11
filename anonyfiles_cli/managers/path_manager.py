# anonyfiles_cli/managers/path_manager.py

from pathlib import Path
from typing import Dict, Optional
# C'EST LA LIGNE CLÉ À VÉRIFIER : DOIT ÊTRE UN IMPORT RELATIF AVEC DEUX POINTS (..)
from ..exceptions import FileIOError
from anonyfiles_core.anonymizer.file_utils import (
    timestamp,
    ensure_folder,
    make_run_dir,
    default_output,
    default_mapping,
    default_log,
)


class PathManager:
    """
    Gère la résolution et la création de tous les chemins de fichiers pour une exécution.
    """
    def __init__(self, input_file: Path, base_output_dir: Path, run_id: str, append_timestamp: bool = True):
        """
        Initialise le PathManager.
        :param input_file: Chemin du fichier d'entrée.
        :param base_output_dir: Répertoire de base où les dossiers de run seront créés.
        :param run_id: ID unique pour cette exécution (généralement un timestamp).
        :param append_timestamp: Si un timestamp doit être ajouté aux noms de fichiers par défaut.
        """
        self.input_file = input_file
        self.base_output_dir = base_output_dir
        self.run_id = run_id
        self.append_timestamp = append_timestamp
        self._run_dir: Optional[Path] = None

    @property
    def run_dir(self) -> Path:
        """Retourne le répertoire de run, le crée si nécessaire."""
        if self._run_dir is None:
            self._run_dir = make_run_dir(self.base_output_dir, self.run_id)
        return self._run_dir

    def resolve_paths(
        self,
        output_override: Optional[Path],
        mapping_override: Optional[Path],
        log_entities_override: Optional[Path],
        dry_run: bool,
        bundle_override: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Résout tous les chemins de fichiers de sortie.
        Si un chemin n'est pas fourni, un chemin par default est généré dans le répertoire de run.
        :param output_override: Chemin du fichier de sortie spécifié par l'utilisateur.
        :param mapping_override: Chemin du fichier de mapping spécifié par l'utilisateur.
        :param log_entities_override: Chemin du fichier de log des entités spécifié par l'utilisateur.
        :param dry_run: Si True, ne crée pas de répertoires pour les chemins par default.
        :return: Un dictionnaire contenant les chemins résolus.
        """
        paths: Dict[str, Path] = {}

        # Chemin du fichier de sortie anonymisé
        if output_override:
            paths["output_file"] = output_override
            # Assurer que le dossier parent existe si l'utilisateur spécifie un chemin
            if not dry_run:
                try:
                    ensure_folder(output_override.parent)
                except Exception as e:
                    raise FileIOError(f"Impossible de créer le répertoire parent pour le fichier de sortie '{output_override}': {e}")
        else:
            if not dry_run: # Ne générer de chemin par défaut que si on va écrire
                paths["output_file"] = default_output(self.input_file, self.run_dir, self.append_timestamp)
            else:
                # En dry_run, si non spécifié, le chemin par default ne sera pas utilisé pour l'écriture
                # On peut le laisser à None ou un chemin "virtuel" si besoin
                paths["output_file"] = self.base_output_dir / "dry_run_output.tmp" # Chemin factice

        # Chemin du fichier de mapping
        if mapping_override:
            paths["mapping_file"] = mapping_override
            if not dry_run:
                try:
                    ensure_folder(mapping_override.parent)
                except Exception as e:
                    raise FileIOError(f"Impossible de créer le répertoire parent pour le fichier de mapping '{mapping_override}': {e}")
        else:
            if not dry_run:
                paths["mapping_file"] = default_mapping(self.input_file, self.run_dir)
            else:
                paths["mapping_file"] = self.base_output_dir / "dry_run_mapping.tmp"

        # Chemin du fichier de log des entités
        if log_entities_override:
            paths["log_entities_file"] = log_entities_override
            if not dry_run:
                try:
                    ensure_folder(log_entities_override.parent)
                except Exception as e:
                    raise FileIOError(f"Impossible de créer le répertoire parent pour le fichier de log '{log_entities_override}': {e}")
        else:
            if not dry_run:
                paths["log_entities_file"] = default_log(self.input_file, self.run_dir)
            else:
                paths["log_entities_file"] = self.base_output_dir / "dry_run_log.tmp"

        # Chemin du bundle zip
        if bundle_override:
            paths["bundle_file"] = bundle_override
            if not dry_run:
                try:
                    ensure_folder(bundle_override.parent)
                except Exception as e:
                    raise FileIOError(f"Impossible de créer le répertoire parent pour le bundle '{bundle_override}': {e}")
        else:
            if not dry_run:
                paths["bundle_file"] = self.run_dir / f"{self.input_file.stem}_bundle.zip"
            else:
                paths["bundle_file"] = self.base_output_dir / "dry_run_bundle.tmp"

        # Le répertoire de run lui-même (s'il n'est pas déjà créé par les chemins spécifiés par l'utilisateur)
        if not dry_run:
            try:
                _ = self.run_dir
            except Exception as e:
                raise FileIOError(f"Impossible de créer le répertoire de run '{self.run_dir}': {e}")

        return paths
