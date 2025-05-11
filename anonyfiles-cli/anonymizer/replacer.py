# anonymizer/replacer.py
from faker import Faker
faker = Faker("fr_FR")

# Dictionnaires et compteurs globaux pour maintenir l'état entre les appels
# à generate_replacements *dans une même exécution du script*.
# Cela assure que le même nom original reçoit toujours le même code d'anonymisation
# et que le même texte d'entité (LOC, DATE, etc.) reçoit toujours le même remplacement Faker généré.

# Pour le type 'codes' (principalement pour PER)
person_code_map: Dict[str, str] = {}
person_counter: int = 0

# Pour le type 'faker' (pour LOC, DATE, EMAIL, etc. si configuré)
faker_consistency_map: Dict[str, str] = {} # Maps original_text -> generated_faker_replacement


def generate_replacements(entities: List[Tuple[str, str]], replacement_rules: Dict[str, Dict[str, Any]]):
    """
    Génère un dictionnaire de remplacements pour les entités détectées,
    en utilisant les règles de remplacement fournies.

    Maintient des remplacements cohérents pour le même texte d'entité original
    en utilisant des dictionnaires globaux (person_code_map, faker_consistency_map).

    Args:
        entities (list): Une liste de tuples (text, label) d'entités détectées uniques
                         sur l'ensemble du document.
        replacement_rules (dict): Un dictionnaire définissant les règles de remplacement
                                  par label d'entité (ex: {"PER": {"type": "codes"}, "LOC": {"type": "faker"}}).

    Returns:
        tuple: Un tuple contenant (replacements_dict, person_code_mapping_dict).
               replacements_dict est le dictionnaire {texte_original_nettoye: remplacement}.
               person_code_mapping_dict est le dictionnaire {Nom Original: Code NOMxxx}.
               La map des codes personne est retournée pour permettre son export.
    """
    global person_code_map
    global person_counter
    global faker_consistency_map

    replacements: Dict[str, str] = {}
    # On retourne toujours la map globale pour s'assurer d'avoir toutes les correspondances
    # même si generate_replacements était appelée plusieurs fois (ce qui n'est pas le cas actuel).


    # Tri les entités par label puis par texte pour assurer un ordre déterministe
    # dans l'attribution des codes/remplacements Faker cohérents.
    sorted_entities = sorted(entities, key=lambda item: (item[1], item[0]))


    for text, label in sorted_entities:
        clean_text = text.strip()

        # Vérifie si un remplacement a déjà été généré pour ce texte nettoyé spécifique.
        if clean_text in replacements:
            continue # Passe si déjà traité


        # --- Déterminer la règle de remplacement pour ce label ---
        # Utilise la règle spécifique au label, ou une règle par défaut si non trouvée
        rule = replacement_rules.get(label, {"type": "redact"}) # Default to redact if no rule specified


        # --- Appliquer la règle de remplacement ---

        if rule["type"] == "codes":
            # Règle pour générer des codes séquentiels (utilisé pour PER)
            if clean_text not in person_code_map:
                person_counter += 1
                prefix = rule.get("options", {}).get("prefix", "NOM")
                padding = rule.get("options", {}).get("padding", 3)
                try:
                    # Use zfill for padding as it's simpler than f-string for variable padding
                    code = f"{prefix}{str(person_counter).zfill(padding)}"
                except Exception as e:
                     print(f"Avertissement: Erreur lors du formatage du code pour '{clean_text}'. Utilisation sans padding. {e}")
                     code = f"{prefix}{person_counter}" # Fallback
                person_code_map[clean_text] = code # Store mapping globally

            # Récupère le code attribué
            replacement_text = person_code_map.get(clean_text, "[CODE_ERROR]") # Fallback in case of logic error

        elif rule["type"] == "faker":
             # Règle pour utiliser Faker avec cohérence
             if clean_text not in faker_consistency_map:
                  # Generate Faker replacement based on label
                  # This part needs specific Faker calls per label type
                  faker_replacement = "[FAKER_REDACTED]" # Default fallback
                  if label == "PER": # Although PER usually uses 'codes', handle if configured otherwise
                      faker_replacement = faker.name()
                  elif label == "LOC":
                      faker_replacement = faker.city()
                  elif label == "ORG":
                      faker_replacement = faker.company() # Use company for ORG
                  elif label == "DATE":
                      faker_replacement = faker.date()
                  elif label == "EMAIL":
                      faker_replacement = faker.email()
                  # Add other specific faker calls here based on labels you expect

                  faker_consistency_map[clean_text] = faker_replacement # Store mapping globally

             # Récupère le remplacement Faker attribué
             replacement_text = faker_consistency_map.get(clean_text, "[FAKER_ERROR]") # Fallback


        elif rule["type"] == "redact":
            # Règle pour remplacer par un texte fixe
            replacement_text = rule.get("options", {}).get("text", "[REDACTED]")

        elif rule["type"] == "placeholder":
             # Règle pour remplacer par un placeholder basé sur le label
             format_string = rule.get("options", {}).get("format", "[{}_ANONYME]")
             try:
                 replacement_text = format_string.format(label)
             except Exception:
                 replacement_text = "[INVALID_PLACEHOLDER_FORMAT]"


        else:
            # Type de règle inconnu, utiliser le remplacement par défaut [REDACTED]
            typer.secho(f"Avertissement : Type de remplacement inconnu '{rule['type']}' pour l'entité '{clean_text}' ({label}). Utilisation de [REDACTED].", fg=typer.colors.YELLOW)
            replacement_text = "[REDACTED]"


        # Ajoute le remplacement généré au dictionnaire principal
        replacements[clean_text] = replacement_text


    # Retourne le dictionnaire principal des remplacements ET la map des codes personne (pour export)
    return replacements, person_code_map