# anonymizer/replacer.py
from faker import Faker
faker = Faker("fr_FR")

# Dictionnaires et compteurs globaux pour maintenir l'état entre les appels
# à generate_replacements. Cela assure que le même nom original reçoit
# toujours le même code d'anonymisation (ou le même remplacement Faker si consistant).

# Map pour stocker la correspondance entre le texte original d'une personne et son code NOMxxx
person_code_map = {}
# Compteur pour générer les codes NOMxxx séquentiellement
person_counter = 0

# Note : Pour les autres types d'entités (LOC, DATE, EMAIL), la génération Faker
# actuelle produit un remplacement potentiellement différent à chaque appel pour le même
# texte original (ex: 'Paris' peut devenir 'Lyon' une fois, puis 'Nice' une autre fois
# si generate_replacements était appelée plusieurs fois avec 'Paris' en entrée).
# Si vous avez besoin de consistency pour ces autres types aussi ('Paris' toujours remplacé
# par la même fausse ville), il faudrait ajouter des maps similaires (loc_map, date_map, email_map)
# et vérifier/stocker les remplacements générés par Faker dans ces maps avant de les ajouter à 'replacements'.
# Pour l'instant, l'implémentation ci-dessous se concentre sur la génération de codes consistants pour 'PER'.


def generate_replacements(entities):
    """
    Génère un dictionnaire de remplacements pour les entités détectées.
    Pour les entités de type 'PER' (personne), génère un code séquentiel (NOM001, NOM002, ...).
    Pour les autres entités, utilise faker ou un espace réservé [REDACTED].

    Maintient des remplacements cohérents pour le même texte d'entité original
    en utilisant des dictionnaires globaux.

    Args:
        entities (list): Une liste de tuples (text, label) d'entités détectées uniques.
                         Cette liste est censée contenir des paires (texte, label) uniques
                         dérivées des entités de l'ensemble du document.

    Returns:
        tuple: Un tuple contenant (replacements_dict, person_code_mapping_dict).
               replacements_dict est un dictionnaire où les clés sont les textes
               d'entités originaux (nettoyés des espaces) et les valeurs sont leurs remplacements.
               person_code_mapping_dict est un dictionnaire {Nom Original: Code NOMxxx}
               contenant la table de correspondance pour les personnes.
    """
    global person_code_map
    global person_counter
    # global loc_map # Décommenter si ajout de la cohérence pour LOC etc.
    # global date_map
    # global email_map


    replacements = {}


    # Tri les entités par label puis par texte pour assurer un ordre déterministe
    # dans l'attribution des codes (NOM001, NOM002... seront toujours attribués
    # aux mêmes noms si le traitement est relancé sur le même fichier).
    # Note : ce tri est sur les entités *uniques* passées en entrée
    sorted_entities = sorted(entities, key=lambda item: (item[1], item[0]))


    for text, label in sorted_entities:
        # Utilise la version nettoyée (sans espaces début/fin) du texte comme clé de map.
        # Cela aide à gérer les éventuels espaces ajoutés par la détection.
        clean_text = text.strip()

        # Vérifie si un remplacement a déjà été généré pour ce texte nettoyé spécifique.
        # Cela peut arriver si le même texte est étiqueté avec plusieurs labels par spaCy,
        # ou si une exécution précédente de la fonction (bien qu'elle ne soit appelée
        # qu'une seule fois dans le main actuel) a déjà traité ce texte.
        if clean_text in replacements:
            continue # Passe si déjà traité

        # --- Logique de remplacement par type d'entité ---

        if label == "PER":
            # Traitement spécifique pour les personnes : génération de code séquentiel
            if clean_text not in person_code_map:
                # Nouveau nom de personne unique rencontré, attribue le code suivant
                person_counter += 1
                # Formate le code - utilise 3 chiffres avec padding (NOM001, NOM002...) par défaut.
                # Ajuster le padding {person_counter:04} pour gérer jusqu'à 9999 noms uniques, etc.
                # Si plus de 999 noms uniques sont présents et que le padding reste à 03,
                # les codes passeront à NOM1000, NOM1001 sans padding initial.
                code = f"NOM{person_counter:03}"
                person_code_map[clean_text] = code # Stocke la correspondance nom original -> code globalement
            else:
                # Nom de personne unique déjà vu, récupère son code attribué globalement
                code = person_code_map[clean_text]

            # Ajoute le remplacement par code dans le dictionnaire principal des remplacements
            replacements[clean_text] = code

        elif label == "LOC":
            # Remplacement par une ville Faker (peut être inconsistante si le même nom
            # de lieu apparaît plusieurs fois et que la cohérence n'est pas ajoutée)
            # Pour une cohérence:
            # if clean_text not in loc_map: loc_map[clean_text] = faker.city()
            # replacements[clean_text] = loc_map[clean_text]
            # Implémentation actuelle simple :
            replacements[clean_text] = faker.city()

        elif label == "DATE":
            # Remplacement par une date Faker (peut être inconsistante)
             replacements[clean_text] = faker.date()
             # Pour une cohérence:
            # if clean_text not in date_map: date_map[clean_text] = faker.date()
            # replacements[clean_text] = date_map[clean_text]


        elif label == "EMAIL":
            # Remplacement par un email Faker (peut être inconsistante)
             replacements[clean_text] = faker.email()
             # Pour une cohérence:
            # if clean_text not in email_map: email_map[clean_text] = faker.email()
            # replacements[clean_text] = email_map[clean_text]

        else:
            # Remplacement par défaut pour les autres types d'entités non gérés spécifiquement
            # On pourrait inclure le label pour info : f"[REDACTED_{label}]"
            replacements[clean_text] = "[REDACTED]"

    # Retourne les remplacements ET la table de correspondance pour les personnes
    return replacements, person_code_map # Retourne la map globale pour s'assurer que toutes les correspondances sont incluses