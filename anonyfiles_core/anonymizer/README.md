# 🧠 Anonymizer Core

Ce dossier contient le cœur du moteur d'anonymisation.

## 📂 Rôle

Il implémente la logique pure de détection et de remplacement, indépendante de l'interface (CLI ou API).

## 📄 Composants

- **Detection** (`ner_processor.py`, `spacy_engine.py`) : reconnaissance d'entités
  nommées via spaCy, complétée par des regex prioritaires (`EMAIL`, `DATE`,
  `PHONE`, `IBAN` et désormais `ADDRESS`).
- **Mode strict** (`ner_processor.py`) : activé par `strict_mode`, il ajoute des
  heuristiques plus agressives quand une fuite coûte plus cher qu'un faux positif :
  prénoms français isolés, adresses probables, téléphones variés, emails obfusqués
  (`nom [at] domaine [point] fr`), acronymes/lignes en majuscules et valeurs
  sensibles dans des lignes contextualisées (`Nom:`, `Adresse:`, `Tel:`, `Email:`,
  `Dossier:`…).
- **Ajout manuel d'entités** (`engine.py`, `add_manual_entities_to_detected_entities`) :
  injecte les entités fournies par l'utilisateur (texte exact + label) dans les
  blocs détectés, sans chevaucher les détections existantes.
- **Remplacement** : stratégies de masquage (codes séquentiels, Faker, redact,
  placeholder).
- **Orchestration** (`engine.py`, `AnonyfilesEngine`) : coordination du processus
  d'analyse et de transformation.
- **Scanner anti-fuite** (`privacy_warning_scanner.py`) : après anonymisation,
  re-scanne la sortie finale pour repérer les valeurs sensibles résiduelles
  (emails, téléphones, IBAN, adresses, prénoms capitalisés, acronymes). Il ignore
  les placeholders et les valeurs de remplacement générées pour limiter les faux
  positifs, puis remonte `privacy_warnings` (+ `privacy_warnings_count`) dans la
  réponse du moteur, sans bloquer le résultat.
- **PDF** : Redaction PyMuPDF sur les coordonnées du texte original, avec suppression
  du texte sensible extractible dans le PDF final.
- **Typage progressif** : `mypy` couvre les types partagés, processors formats,
  factory et writer via la cible configurée dans `pyproject.toml`.
