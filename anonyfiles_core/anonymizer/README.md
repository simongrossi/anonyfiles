# 🧠 Anonymizer Core

Ce dossier contient le cœur du moteur d'anonymisation.

## 📂 Rôle

Il implémente la logique pure de détection et de remplacement, indépendante de l'interface (CLI ou API).

## 📄 Composants

- **Detection** : Utilisation de spaCy pour la reconnaissance d'entités nommées (NER).
- **Remplacement** : Stratégies de masquage (Faker, hashing, masquage simple).
- **Orchestration** : Coordination du processus d'analyse et de transformation.
- **PDF** : Redaction PyMuPDF sur les coordonnées du texte original, avec suppression
  du texte sensible extractible dans le PDF final.
- **Typage progressif** : `mypy` couvre les types partagés, processors formats,
  factory et writer via la cible configurée dans `pyproject.toml`.
