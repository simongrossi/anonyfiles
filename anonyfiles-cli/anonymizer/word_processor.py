from docx import Document
import os
from .anonymizer_core import apply_positional_replacements # Importer la fonction de remplacement positionnel

def extract_text_from_docx(path):
    """Extrait le texte d'un fichier .docx, paragraphe par paragraphe."""
    doc = Document(path)
    # Pour l'instant, on retourne juste le texte, main.py détectera les entités avec offsets
    return [p.text for p in doc.paragraphs]

# Modifier la signature pour accepter la liste des entités avec offsets par paragraphe
def replace_entities_in_docx(input_path, output_path, replacements, entities_per_paragraph_with_offsets):
    """
    Remplace les entités dans un fichier .docx à l’aide de la table de remplacements
    en utilisant le remplacement basé sur la position pour chaque paragraphe.
    """
    doc = Document(input_path)
    paragraphs = doc.paragraphs

    # Vérifier si le nombre de paragraphes correspond au nombre de listes d'entités fournies
    if len(paragraphs) != len(entities_per_paragraph_with_offsets):
        # Cela indique un problème dans la logique de détection de main.py
        # Gérer cette erreur ou lever une exception
        print(f"Erreur: Le nombre de paragraphes ({len(paragraphs)}) ne correspond pas au nombre de listes d'entités fournies ({len(entities_per_paragraph_with_offsets)}).")
        # Pour l'instant, on pourrait choisir de ne pas traiter le fichier ou de continuer avec un avertissement.
        # Ici, on va lever une erreur pour signaler le problème.
        raise ValueError("Mismatch between paragraph count and entity list count.")


    if not paragraphs or all(not p.text.strip() for p in paragraphs):
        doc.save(output_path)
        return

    # Parcourir les paragraphes et leurs listes d'entités correspondantes
    for i, p in enumerate(paragraphs):
        original_text = p.text
        entities_for_this_paragraph = entities_per_paragraph_with_offsets[i]

        if original_text.strip() and entities_for_this_paragraph:
            # Appliquer le remplacement basé sur la position au texte du paragraphe
            anonymized_text = apply_positional_replacements(
                original_text,
                replacements, # Utiliser la table de remplacements globale
                entities_for_this_paragraph # Utiliser les entités AVEC offsets pour ce paragraphe
            )
        else:
            # Si le paragraphe est vide ou ne contient pas d'entités à remplacer dans cette passe
            anonymized_text = original_text # Conserver le texte original

        # Remplacer le contenu du paragraphe avec le texte anonymisé
        # Attention: Cette méthode supprime tout le formatage du paragraphe d'origine.
        for run_element in p._element.xpath('./w:r'):
            run_element.getparent().remove(run_element)

        if anonymized_text.strip():
            p.add_run(anonymized_text)
        # else: Si le texte anonymisé est vide, le paragraphe sera vidé

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    doc.save(output_path)