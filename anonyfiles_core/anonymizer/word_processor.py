# anonymizer/word_processor.py

from pathlib import Path
import logging
from docx import Document
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

logger = logging.getLogger(__name__)


class DocxProcessor(BaseProcessor):
    """
    Processor pour les fichiers .docx.
    - Traverse hiérarchiquement : Paragraphes du corps -> Tableaux (récursifs).
    - Préserve l'intégrité de la structure tout en anonymisant l'ensemble du contenu.
    """

    def _iter_block_items(self, parent_elt):
        """
        Générateur récursif qui parcourt tous les éléments contenant du texte
        (Paragraphes directs, et Cellules de Tableaux) dans un ordre déterministe.
        """
        # 1. Paragraphes directs
        if hasattr(parent_elt, 'paragraphs'):
            for paragraph in parent_elt.paragraphs:
                yield paragraph
        
        # 2. Tableaux (qui contiennent des lignes -> cellules -> paragraphes/tables)
        if hasattr(parent_elt, 'tables'):
            for table in parent_elt.tables:
                for row in table.rows:
                    for cell in row.cells:
                        # Récursion: une cellule contient des paragraphes et potentiellement d'autres tables
                        yield from self._iter_block_items(cell)

    def extract_blocks(self, input_path):
        """
        Extrait TOUS les blocs de texte (Body + Tables).
        Retourne une liste plate de chaînes de caractères.
        """
        doc = Document(input_path)
        blocks = []
        
        # Le Document est le parent racine
        for paragraph in self._iter_block_items(doc):
            blocks.append(paragraph.text)
            
        return blocks

    def replace_entities(
        self, input_path, output_path, replacements, entities_per_block_with_offsets
    ):
        """
        [Legacy method] Remplace les entités in-place et sauvegarde.
        """
        doc = Document(input_path)
        
        # On récupère tous les paragraphes cibles dans le même ordre
        target_paragraphs = list(self._iter_block_items(doc))

        if len(target_paragraphs) != len(entities_per_block_with_offsets):
            logger.warning(
                f"Mismatch Word: {len(target_paragraphs)} paragraphes trouvés vs {len(entities_per_block_with_offsets)} listes d'entités."
            )
            # On continue, mais risque de désalignement si le fichier a changé entre temps (peu probable ici)

        for i, p in enumerate(target_paragraphs):
            # Sécurité index
            if i >= len(entities_per_block_with_offsets):
                break
                
            original_text = p.text
            entities_for_this_paragraph = entities_per_block_with_offsets[i]

            anonymized_text = original_text
            if original_text.strip() and entities_for_this_paragraph:
                anonymized_text = apply_positional_replacements(
                    original_text, replacements, entities_for_this_paragraph
                )

            # Application du remplacement
            # Stratégie simple : si changement, on remplace le texte.
            # Pour essayer de garder le style, on peut clear et add_run, mais attention aux formats complexes.
            if anonymized_text != original_text:
                # Méthode brute propre :
                # p.text = anonymized_text  <-- perd les styles de runs multiples
                
                # Méthode qui essaie de préserver le style du premier run ou ajoute un nouveau run
                # Todo: Une reconstruction "Run-aware" nécessiterait un parser beaucoup plus complexe (mapping offset -> run).
                # Pour l'instant, on applique la méthode standard du projet : vidage des runs et ajout du nouveau texte.
                
                # Vider les runs existants
                p.clear() 
                # (Note : p.clear() n'existe pas nativement sur Paragraph dans toutes les versions, 
                # souvent on fait p._element.clear_content() ou boucle remove)
                
                # Alternative robuste compatible python-docx standard:
                for run in p.runs:
                    run.text = ""
                
                # On remet tout le texte dans le premier run s'il existe (garde le style du début), sinon on en crée un.
                if p.runs:
                    p.runs[0].text = anonymized_text
                else:
                    p.add_run(anonymized_text)

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        doc.save(output_path)

    def reconstruct_and_write_anonymized_file(
        self, output_path, final_processed_blocks, original_input_path, **kwargs
    ):
        """
        Reconstruit le document DOCX en injectant les blocs anonymisés.
        Gère le corps du texte ET les tableaux.
        """
        doc = Document(original_input_path)
        target_paragraphs = list(self._iter_block_items(doc))
        
        count_expected = len(target_paragraphs)
        if count_expected != len(final_processed_blocks):
             logger.warning(
                "Mismatch Reconstruct Word: %s paragraphes (inclus tableaux) vs %s blocs fournis.",
                count_expected,
                len(final_processed_blocks)
            )

        for i, p in enumerate(target_paragraphs):
            if i >= len(final_processed_blocks):
                break
                
            new_text = final_processed_blocks[i]
            
            # Si le texte n'a pas changé, on ne touche à rien (préserve 100% du formatage complexe)
            if p.text == new_text:
                continue
                
            # Logique de conservation des styles (Run distribution)
            # On essaie de répartir le nouveau texte dans les runs existants
            runs = p.runs
            if not runs:
                if new_text:
                    p.add_run(new_text)
                continue

            # Si on a du texte à écrire
            # Approche simple et robuste pour éviter les corruptions XML :
            # 1. On calcule la longueur totale disponible dans les runs actuels ? Non, le texte change de taille.
            # 2. Approche "Buckets" : on remplit les runs un par un avec le nouveau texte.
            
            remaining_text = new_text
            for run in runs:
                if not remaining_text:
                    # Plus de texte à mettre, on vide ce run (il devient invisible)
                    run.text = ""
                    continue
                
                # Décision arbitraire : on essaie de mettre autant de caractères qu'il y en avait ?
                # Ou on met tout dans le premier ?
                # Mettre tout dans le premier est le plus sûr pour la lisibilité, 
                # mais "répartir" aide parfois si le mot en gras était au milieu.
                # Vu qu'on anonymise, la structure sémantique change. "Jean Dupont" (Gras) devient "PER_1" (Gras).
                # Le plus simple est de tout mettre dans le run[0] et vider les autres, 
                # OU d'utiliser une logique proportionnelle simple.
                
                # Gardons la logique du code précédent qui semblait vouloir préserver "autant que possible".
                # MAIS pour plus de fiabilité sur la donnée (éviter de couper au milieu d'un run),
                # la méthode la plus sûre pour l'ETL est :
                # - Run 1 reçoit tout le texte (hérite du style du début de phrase)
                # - Runs suivants vidés.
                
                # SAUF si l'ancien code avait une meilleure logique.
                # L'ancien code faisait :
                # if pointer < len(new_text): runs[-1].text += new_text[pointer:]
                # Reprenons cette logique "bucket" simple qui préserve la longueur visuelle relative :
                
                run_len = len(run.text)
                # Si le run était vide, on n'y met rien sauf si c'est le dernier et qu'il reste du texte
                if run_len == 0:
                    run.text = "" 
                else:
                    # On prend une tranche
                    chunk = remaining_text[:run_len]
                    run.text = chunk
                    remaining_text = remaining_text[run_len:]
            
            # S'il reste du texte après avoir rempli tous les slots existants, on l'ajoute au dernier run
            if remaining_text and runs:
                runs[-1].text += remaining_text
        
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        doc.save(output_path)
