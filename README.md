# 🕵️‍♂️ anonyfiles

**anonyfiles** est un outil open source de référence pour anonymiser automatiquement des documents texte, tableurs ou bureautiques via une ligne de commande performante (CLI) et une interface graphique moderne (GUI). Il exploite le NLP (avec **spaCy**) et génère des données factices réalistes (**Faker**).

---

## 📌 Sommaire

- [🎯 Objectif](#-objectif)
- [🚀 Fonctionnalités](#-fonctionnalités)
- [💻 Prérequis](#-prérequis)
- [⚙️ Installation CLI](#-installation-cli)
- [🛠️ Configuration](#-configuration)
- [🧩 Architecture](#-architecture)
- [💡 Utilisation CLI](#-utilisation-cli)
- [🔍 Entités supportées](#-entités-supportées)
- [🗂️ Structure du projet CLI](#-structure-du-projet-cli)
- [🖼️ Structure du projet GUI](#-structure-du-projet-gui)
- [📊 Feuille de route (Roadmap)](#-feuille-de-route-roadmap)
- [🤝 Contribution](#-contribution)
- [📝 Changelog](#-changelog)
- [🛡️ Licence](#-licence)

---

## 🎯 Objectif

Anonymiser rapidement et efficacement des documents `.docx`, `.xlsx`, `.csv`, `.txt` en remplaçant les entités sensibles (noms, lieux, dates, emails...) tout en conservant la structure et la lisibilité des fichiers.

---

## 🚀 Fonctionnalités

| Fonction                  | Description |
|--------------------------|-------------|
| Formats supportés        | `.docx`, `.xlsx`, `.csv`, `.txt`, `.pdf`, `.json` |
| Détection NER            | SpaCy `fr_core_news_md` |
| Détection EMAIL & DATE   | Regex robuste intégrée, tous formats de date classiques |
| Remplacement positionnel | Respect strict des offsets `start_char` / `end_char` |
| Données de remplacement  | Faker (`fr_FR`), `[REDACTED]`, codes séquentiels (`NOMnnn`), placeholder |
| Fichier config YAML      | Modèle, entités, règles et options configurables |
| **Config Remplacement**  | **Configuration fine par type d'entité via YAML** |
| **Filtre d’exclusion**   | **Filtre d’exclusion configurable (YAML/CLI) pour éviter les faux positifs** |
| Mode simulation (`--dry-run`) | Analyse sans écriture dans les fichiers |
| Export CSV/JSON          | Journalisation détaillée des entités détectées |
| **Export Mapping Codes** | **Table Nom Original → Code pour désanonymisation et audit** |
| Interface graphique (GUI)| Drag & drop, sélection visuelle des entités à anonymiser |

---

## 💻 Prérequis

- Python ≥ 3.8 (recommandé 3.11 pour compatibilité optimale)
- pip
- **PyYAML**, **Typer**, **Faker**, **python-docx**, **pandas**, **openpyxl** (via `requirements.txt`)
- Node.js + Rust (pour la GUI)

---

## ⚙️ Installation CLI

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
python3.11 -m venv .venv
source .venv/bin/activate      # ou .venv\Scriptsctivate sous Windows
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

---

## 🛠️ Configuration

anonyfiles utilise un fichier YAML pour définir :
- le modèle spaCy,
- les entités à cibler,
- les règles de remplacement,
- les entités à exclure de l’anonymisation (couples Texte, Label).

> Voir un exemple dans `config.yaml.sample`.

**Exemple :**

```yaml
spacy_model: fr_core_news_md

replacements:
  PER:
    type: codes
  LOC:
    type: faker
    options:
      locale: fr_FR
      provider: address
  ORG:
    type: redact
    options:
      text: "[ENTREPRISE]"
  DATE:
    type: redact
    options:
      text: "[REDACTED_DATE]"

exclude_entities:
  - [Date, PER]
  # Ajoutez d'autres couples [Texte, Label] si besoin
```

---

## 🧩 Architecture

Le projet est organisé autour d’une architecture modulaire et factorisée pour assurer robustesse et extensibilité :

- **Pipeline métier central (`AnonyfilesEngine`)**
  - Orchestration unique de l’anonymisation : détection des entités, génération des remplacements, application selon format.
- **Processors spécialisés par format**
  - Chaque format supporté (`.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`) possède un *processor* dédié héritant d’une interface commune (`BaseProcessor`), qui définit l’extraction et le remplacement positionnel.
- **Gestion des remplacements**
  - Moteur de remplacement configurable via YAML et CLI, supportant Faker, codes séquentiels, redaction et placeholders.
- **Support PDF avancé**
  - Anonymisation par annotations PyMuPDF, pour masquer les zones sensibles sans altérer la mise en page.
- **Tests unitaires**
  - Chaque composant (processor, core, utils) dispose de tests unitaires garantissant la stabilité et facilitant les évolutions.
- **CLI légère**
  - Interface en ligne de commande via Typer, déléguant toute la logique métier au core.
- **Organisation pratique des fichiers**
  - `input_files/`, `output_files/`, `log/` et `mappings/` pour les fichiers sources, résultats et journaux.

Cette architecture permet d’ajouter facilement de nouveaux formats, de configurer finement les règles d’anonymisation et de maintenir le projet efficacement.

---

## 💡 Utilisation CLI

Lance le script principal pour anonymiser ou désanonymiser un fichier selon la configuration YAML (ou les options CLI).

**Principales options :**

| Option                | Description |
|-----------------------|-------------|
| `--config PATH`       | Fichier YAML de configuration |
| `-o, --output`        | Fichier de sortie |
| `-l, --log-entities`  | CSV des entités détectées |
| `--mapping-output`    | CSV du mapping Nom original → Code |
| `--dry-run`           | Simule, pas d’écriture |
| `--exclude-entity`    | Entité à exclure sous la forme "Texte,Label" (plusieurs fois) |
| `-e, --entities`      | Limite aux types d'entités (PER, LOC, ORG, DATE, EMAIL...) |

## 🗂️ Support avancé des fichiers CSV

Par défaut, anonyfiles considère que votre fichier CSV possède une première ligne d’entête (noms de colonnes) **qui ne sera jamais anonymisée**.

### ➡️ Option : `--csv-no-header`

Si votre CSV **ne possède pas d’entête** (la première ligne contient des données), ajoutez l’option :

```bash
python main.py anonymize input.csv --config generated_config.yaml -o output_anonymise.csv --csv-no-header

### Anonymisation

```bash
python main.py anonymize input_files/message.txt   --config generated_config.yaml   -o output_files/message_anonymise.txt   --log-entities log/entities.csv   --mapping-output mappings/mapping.csv
```

### Désanonymisation

```bash
python main.py deanonymize output_files/message_anonymise.txt   --mapping-csv mappings/mapping.csv   -o output_files/message_restored.txt
```

**Exemples :**

```bash
python main.py anonymize input_files/message.txt -o output_files/anonymise.txt --log-entities log/entities.csv
python main.py anonymize input_files/message.txt --exclude-entity "Date,PER"
python main.py anonymize input_files/rapport.docx --config config.yaml --mapping-output log/mapping.csv
```

---

### 🔁 Règles de remplacement (YAML)

- `type: codes` → Code unique (NOM001)
- `type: faker` → Données factices (faker)
- `type: redact` → Texte fixe
- `type: placeholder` → [LABEL]
- Défaut : `[REDACTED]`

---

## 🔍 Entités supportées

| Code | Type         | Source       | Remplacement par défaut                   |
|------|--------------|-------------|-------------------------------------------|
| PER  | Personne     | spaCy       | code séquentiel (NOMnnn)                  |
| LOC  | Lieu         | spaCy       | Faker                                     |
| ORG  | Organisation | spaCy       | `[REDACTED]`                              |
| DATE | Date         | Regex/spaCy | `[REDACTED_DATE]` ou Faker                |
| EMAIL| Email        | Regex       | Faker                                     |
| MISC | Divers       | spaCy       | `[REDACTED]` (autres entités non catégorisées) |

---

## 🗂️ Structure du projet CLI

```text
anonyfiles/
├── main.py                 # Script principal CLI (Typer)
├── requirements.txt        # Dépendances Python
├── config.yaml.sample      # Exemple de fichier de configuration YAML
│
├── anonymizer/             # Logique métier d’anonymisation
│   ├── anonyfiles_core.py  # Orchestration pipeline factorisé (core)
│   ├── spacy_engine.py     # Chargement modèle spaCy, NER + regex emails/dates
│   ├── replacer.py         # Gestion des règles de remplacement (faker, codes, redact, placeholder)
│   ├── word_processor.py   # Processor pour fichiers Word (.docx)
│   ├── excel_processor.py  # Processor pour fichiers Excel (.xlsx)
│   ├── csv_processor.py    # Processor pour fichiers CSV (.csv)
│   ├── txt_processor.py    # Processor pour fichiers texte (.txt)
│   ├── utils.py            # Fonctions utilitaires (offsets, remplacements)
│
├── input_files/            # Dossier d’entrée pour fichiers à anonymiser
├── output_files/           # Dossier de sortie pour fichiers anonymisés
├── log/                    # Logs des entités détectées
├── mappings/               # Fichiers de mapping pour désanonymisation
├── tests/                  # Tests unitaires et scripts de génération
```

---

## 🖼️ Structure du projet GUI

```text
anonyfiles-gui/
├── src/                    # Frontend React (TypeScript)
│   ├── App.tsx             # Point d'entrée principal
│   ├── components/         # Composants réutilisables (Dropzone, boutons, progress bar, etc.)
│   ├── pages/              # Pages principales (Accueil, Résultats, Paramètres…)
│   ├── styles/             # Feuilles de style (Tailwind CSS ou CSS modules)
│   ├── utils/              # Fonctions utilitaires frontend
│   └── index.tsx           # Point de montage ReactDOM
│
├── public/                 # Fichiers statiques (favicon, HTML, images…)
├── dist/                   # Dossier de build frontend (ne pas versionner)
│
├── package.json            # Dépendances npm et scripts
├── vite.config.ts          # Configuration du bundler Vite.js
│
└── src-tauri/              # Backend Rust via Tauri
    ├── src/
    │   └── main.rs         # Logiciel backend principal
    ├── tauri.conf.json     # Config globale Tauri
    └── target/             # Binaries compilés (ne pas versionner)
```

---

## 📊 Feuille de route (Roadmap)

Le projet évolue en continu, voici la priorisation des prochaines phases de développement :

| Priorité | Thème                | État      | Commentaire / Lien tâche |
|----------|----------------------|-----------|-------------------------|
| 1        | Robustesse multi-format (TXT, CSV, DOCX, XLSX) | ✅ Fait | Moteur factorisé, détection regex/NER commune |
| 2        | Remplacement positionnel fiable                 | ✅ Fait | Offsets stricts dans tous les formats |
| 3        | Détection universelle des dates et emails       | ✅ Fait | Regex avancée + spaCy |
| 4        | Performance / gestion mémoire                   | 🔜 À venir | Streaming, lazy processing |
| 5        | Règles de remplacement par type (YAML)          | ✅ Fait | Faker, code, redact, placeholder... |
| 6        | Mapping codes <-> originaux                     | ✅ Fait | Export CSV pour désanonymisation possible |
| 7        | Filtre exclusion (YAML / CLI)                   | ✅ Fait | Configurable, évite faux positifs |
| 8        | Support PDF / JSON                              | 🔜 À venir | PDF natif |
| 9        | Désanonymisation CLI (mapping inverse)          | 🔜 À venir | Recherche mapping et restauration |
| 10       | GUI avancée (drag & drop, prévisualisation)     | 🔜 Alpha | Structure Tauri prête, développement en cours |

---

## 🤝 Contribution

1. Fork
2. Branche `feature/xxx` ou `fix/xxx`
3. Tests unitaires
4. Pull Request

---

## 📝 Changelog

### v1.6.0 - 2025-05-16

- **Nouvelle commande CLI `deanonymize`** : restauration de fichiers anonymisés via un fichier mapping CSV.
- **Refactorisation `AnonyfilesEngine`** : gestion améliorée des mappings, exclusions d’entités passées en CLI.
- **Validation YAML avec Cerberus** : remplacement de Yamale pour plus de robustesse.
- **Organisation des fichiers mapping** dans un dossier dédié `mappings/` pour plus de clarté.
- **Logs DEBUG ajoutés** pour le contenu du mapping lors de l’anonymisation.
- **Correction de la gestion des chemins** pour éviter les erreurs d’accès fichier.
- **Documentation CLI mise à jour** avec exemples complets d’utilisation.

- **v1.5.0** – Détection universelle des dates et emails (regex), pipeline refactorisée, exclusion configurable (YAML/CLI), assistant CLI de génération et validation de config YAML
- **v1.4.0** – Configuration fine par type d’entité (YAML), logs améliorés, mapping désanonymisation.
- **v1.3.0** – Codes séquentiels pour PER, mapping exportable.
- **v1.2.0** – GUI alpha, config YAML initiale.
- **v1.1.0** – Amélioration CSV/XLSX.
- **v1.0.0** – Première version.

---

## 🛡️ Licence

MIT © 2025 Simon Grossi

---

**Pour toute question, suggestion ou bug, ouvrez une issue ou contactez le mainteneur !**
