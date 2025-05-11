# 🕵️‍♂️ anonyfiles

**anonyfiles** est un outil open source complet pour anonymiser automatiquement des documents texte, tableurs ou bureautiques via une ligne de commande performante (CLI) et une interface graphique moderne (GUI), en s’appuyant sur le NLP avec **spaCy** et des données factices réalistes générées par **Faker**.

---

## 📌 Sommaire

- [🎯 Objectif](#-objectif)
- [🚀 Fonctionnalités](#-fonctionnalités)
- [💻 Prérequis](#-prérequis)
- [⚙️ Installation CLI](#-installation-cli)
- [🛠️ Configuration](#️-configuration)
- [💡 Utilisation CLI](#-utilisation-cli)
- [🔍 Entités supportées](#-entités-supportées)
- [🗂️ Structure du projet](#️-structure-du-projet)
- [🖼️ Interface Graphique (GUI)](#interface-graphique-gui)
- [🧭 Feuille de route (Roadmap)](#-feuille-de-route-roadmap)
- [🤝 Contribution](#-contribution)
- [📝 Changelog](#-changelog)
- [🛡️ Licence](#️-licence)

---

## 🎯 Objectif

Anonymiser rapidement et efficacement des documents `.docx`, `.xlsx`, `.csv`, `.txt` en remplaçant les entités sensibles (noms, lieux, dates, emails...) tout en conservant la structure et la lisibilité des fichiers.

---

## 🚀 Fonctionnalités

| Fonction                  | Description |
|--------------------------|-------------|
| Formats supportés        | `.docx`, `.xlsx`, `.csv`, `.txt` |
| Détection NER            | SpaCy `fr_core_news_md` |
| Détection EMAIL          | Regex robuste intégrée |
| Remplacement positionnel | Respect des offsets `start_char` / `end_char` |
| Données de remplacement  | Faker (fr_FR), `[REDACTED]`, codes séquentiels (NOMnnn), ou placeholder |
| Fichier config YAML      | Modèle, entités, options |
| **NOUVEAU : Config Remplacement** | **Configuration fine des règles de remplacement par type d'entité via fichier YAML** |
| Mode simulation (`--dry`) | Analyse sans écrire |
| Export CSV/JSON          | Journalisation des entités détectées |
| **Export Mapping Codes** | **Export de la table Nom Original -> Code pour désanonymisation des entités remplacées par codes** |
| Interface graphique (GUI) | Drag & drop, sélection visuelle |

---

## 💻 Prérequis

- Python ≥ 3.8 (recommandé 3.11)
- pip
- **NOUVEAU :** PyYAML
- Node.js + Rust (pour la GUI)

---

## ⚙️ Installation CLI

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

---

## 🛠️ Configuration

anonyfiles utilise un fichier de configuration YAML pour définir le modèle spaCy, les entités à cibler et surtout les règles de remplacement spécifiques pour chaque type d'entité.

> Voir exemple complet dans `config.yaml.sample`.

---

## 💡 Utilisation CLI

Commandes disponibles :

```bash
python main.py anonymize input.docx --config config.yaml
```

Options disponibles :
- `--config PATH`
- `-o, --output`
- `-l, --log-entities`
- `--mapping-output`
- `--dry-run`
- `--verbose`

Exemples complets disponibles dans le README initial.

---

## 🔍 Entités supportées

| Code | Type | Source | Remplacement par défaut |
|------|------|--------|--------------------------|
| PER  | Personne | spaCy | code séquentiel |
| LOC  | Lieu     | spaCy | Faker                  |
| ORG  | Organisation | spaCy | `[REDACTED]`       |
| DATE | Date     | spaCy | Faker                  |
| EMAIL| Email    | Regex | Faker                  |
| MISC | Divers   | spaCy | `[REDACTED]`           |

---

# 🕵️‍♂️ anonyfiles

## 🗂️ Structure du projet CLI

```text
anonyfiles/
├── main.py                       # Script principal de la CLI avec Typer (point d’entrée)
├── requirements.txt              # Liste des dépendances Python nécessaires
├── config.yaml.sample            # Exemple complet de fichier de configuration YAML
│
├── anonymizer/                   # Dossier contenant toute la logique métier de l’anonymisation
│   ├── anonymizer_core.py        # (Optionnel/à venir) pour centraliser la logique si besoin
│   ├── spacy_engine.py           # Chargement du modèle spaCy et détection des entités
│   ├── replacer.py               # Génération cohérente des remplacements par règles (faker, codes, etc.)
│   ├── word_processor.py         # Lecture et remplacement d'entités dans les fichiers Word (.docx)
│   ├── excel_processor.py        # Lecture et anonymisation des fichiers Excel (.xlsx)
│   ├── csv_processor.py          # Lecture et traitement des fichiers CSV
│   └── txt_processor.py          # Lecture et anonymisation des fichiers texte (.txt)
│
├── input_files/                  # Répertoire par défaut pour déposer les fichiers à traiter
├── output_files/                 # Dossier de sortie pour les fichiers anonymisés générés
├── log/                          # Répertoire destiné aux logs d’entités et mapping (CSV)
```

---

## 🖼️ Structure du projet GUI

```text
anonyfiles-gui/
├── src/                          # Frontend React en TypeScript
│   ├── App.tsx                   # Point d’entrée principal de l’application
│   ├── components/              # Composants réutilisables (Dropzone, Boutons, Barre de progression, etc.)
│   ├── pages/                   # Pages principales (Accueil, Résultats, Paramètres…)
│   ├── styles/                  # Feuilles de style (via Tailwind CSS ou CSS modules)
│   ├── utils/                   # Fonctions utilitaires frontend
│   └── index.tsx               # Point de montage ReactDOM
│
├── public/                      # Fichiers statiques accessibles (favicon, HTML de base…)
├── dist/                        # Dossier généré lors du build frontend (ne pas versionner)
│
├── package.json                # Dépendances npm et scripts (dev, build, etc.)
├── vite.config.ts              # Configuration du bundler Vite.js
│
└── src-tauri/                   # Backend Rust (intégré via Tauri)
    ├── src/
    │   └── main.rs              # Fichier principal Rust contenant la logique backend
    ├── tauri.conf.json          # Fichier de configuration global de Tauri
    └── target/                  # Fichiers compilés (ne pas versionner)
```

---

✅ Cette structure modulaire permet une séparation claire entre :
- Le **noyau logique** de traitement (dans `anonymizer/`)
- La **gestion de configuration** (via YAML)
- Les **interfaces utilisateur**, avec une CLI robuste et une GUI intuitive
- Une architecture **extensible et maintenable** pour ajouter de nouveaux formats ou comportements

--- 


```text
anonyfiles/
├── main.py
├── requirements.txt
├── config.yaml.sample
│
├── anonymizer/
│   ├── anonymizer_core.py
│   ├── spacy_engine.py
│   ├── replacer.py
│   ├── word_processor.py
│   ├── excel_processor.py
│   ├── csv_processor.py
│   └── txt_processor.py
│
├── input_files/
├── output_files/
├── log/
```

---

## 🖼️ Interface Graphique (GUI)

Développée avec React + Tailwind CSS (frontend) et Tauri en Rust (backend natif).

Structure simplifiée :

```text
anonyfiles-gui/
├── src/
│   ├── App.tsx
│   ├── components/
│   ├── pages/
│   ├── styles/
│   └── utils/
├── public/
├── src-tauri/
│   └── main.rs
├── package.json
├── vite.config.ts
└── README.md
```

Commandes de développement :

```bash
cd anonyfiles-gui
npm install
cargo install tauri-cli
npm run tauri dev
```

---

## 🧭 Feuille de route (Roadmap)

Phase 1 – Robustesse de base
- ✅ Config YAML
- 🔜 Logs & erreurs

Phase 2 – Précision
- 🔜 Préservation .docx
- 🔜 Priorité entités

Phase 3 – Performance
- 🔜 Streaming
- 🔜 Mémoire

Phase 4 – Extensibilité
- 🔜 JSON, PDF
- 🔜 Anonymisation personnalisée

Phase 5 – UX
- 🔜 GUI complète
- 🔜 Documentation Sphinx

---

## 🤝 Contribution

1. Fork
2. Branche `feature/xxx` ou `fix/xxx`
3. Tests unitaires
4. Pull Request

---

## 📝 Changelog

### v1.4.0
- Intégration complète de la configuration YAML
- `--config`, `faker`, `placeholder`, `redact` par entité

### v1.3.0
- Mapping export Nom → Code

### v1.2.0
- GUI alpha, config.yaml.sample

### v1.1.0
- CSV/XLSX améliorés

### v1.0.0
- Version initiale

---

## 🛡️ Licence

MIT © 2025 Simon Grossi
