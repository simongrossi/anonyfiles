# anonymizer/base_processor.py

from typing import List, Any

class BaseProcessor:
    """
    Classe de base pour tout processor de format (TXT, CSV, DOCX, XLSX, etc).
    Définit le contrat minimal à implémenter pour chaque format.
    """

    def extract_blocks(self, input_path) -> List[str]:
        """
        Extrait les blocs de texte à anonymiser depuis le fichier source.
        Peut être une liste de paragraphes, de cellules, ou tout autre découpage logique.
        """
        raise NotImplementedError("extract_blocks doit être implémenté dans chaque processor")

    def replace_entities(
        self,
        input_path,
        output_path,
        replacements,
        entities_per_block_with_offsets: List[List[Any]]
    ):
        """
        Applique le remplacement d'entités (par offsets) sur chaque bloc
        et écrit le résultat dans le fichier de sortie.

        :param input_path: chemin du fichier source
        :param output_path: chemin du fichier de sortie anonymisé
        :param replacements: mapping {texte original -> remplacement}
        :param entities_per_block_with_offsets: liste d'entités avec offsets pour chaque bloc
        """
        raise NotImplementedError("replace_entities doit être implémenté dans chaque processor")
