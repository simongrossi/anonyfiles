# 🧠 Anonymizer Core

Ce dossier contient le cœur du moteur d'anonymisation.

## 📂 Rôle

Il implémente la logique pure de détection et de remplacement, indépendante de l'interface (CLI ou API).

## 📄 Composants

- **Detection** : Utilisation de spaCy pour la reconnaissance d'entités nommées (NER).
- **Remplacement** : Stratégies de masquage (Faker, hashing, masquage simple).
- **Orchestration** : Coordination du processus d'analyse et de transformation.
