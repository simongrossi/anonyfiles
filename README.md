# 🕵️‍♂️ Anonyfiles

**Anonyfiles** est une solution open source complète pour l’anonymisation automatisée de documents texte, tableurs, et bureautiques, basée sur le NLP (spaCy) et des stratégies avancées de remplacement (Faker, codes, placeholders, etc.).

- **CLI (anonyfiles-cli)** : traitement en ligne de commande, configurable, robuste multi-format.
- **GUI (anonyfiles-gui)** : interface graphique moderne (Tauri + Svelte + Rust) pour une anonymisation intuitive, rapide, multiplateforme.

---

## 🚀 Fonctionnalités principales

- Anonymisation de fichiers : `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
- Détection automatique de Noms, Lieux, Organisations, Dates, Emails, etc.
- Stratégies configurables : remplacement factice, [REDACTED], codes séquentiels, etc.
- Mapping complet pour désanonymisation ou audit
- Export CSV des entités détectées
- Sélection fine des entités à anonymiser (interface graphique ou CLI)
- Prise en charge du français (et autres langues via spaCy)
- **Portable** : aucun chemin codé en dur, multiplateforme (Windows, macOS, Linux)

---

## 🗂️ Structure du projet

anonyfiles/
│
├── README.md # Présent fichier
├── anonyfiles-cli/ # Outil en ligne de commande (Python)
│ └── README.md # Doc CLI détaillée
├── anonyfiles-gui/ # Interface graphique Tauri (Svelte/Rust)
│ └── README.md # Doc GUI détaillée
└── ... # Données, configs, tests, docs

---

## 📦 Installation rapide

Voir les README de chaque module :
- [anonyfiles-cli/README.md](./anonyfiles-cli/README.md) pour la CLI
- [anonyfiles-gui/README.md](./anonyfiles-gui/README.md) pour la GUI

---

## 🤝 Contributions

Les contributions sont les bienvenues !  
Voir les sections _Roadmap_, _Contributing_ dans chaque README, ou ouvrez une issue/pull request.

---

## 📜 Licence

Projet sous licence MIT.  
