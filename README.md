
# 🕵️‍♂️ anonyfiles-cli

**anonyfiles-cli** est un outil open source d’anonymisation et de pseudonymisation automatique de documents, en ligne de commande, basé sur **spaCy** et **Faker**, avec une interface GUI en cours de développement.

---

## 📌 Sommaire

- [🎯 Objectif](#-objectif)
- [🚀 Fonctionnalités](#-fonctionnalités)
- [💻 Prérequis](#-prérequis)
- [⚙️ Installation](#-installation)
- [🛠️ Configuration](#️-configuration)
- [💡 Utilisation](#-utilisation)
  - [CLI](#cli)
  - [GUI (alpha)](#gui-alpha)
- [🔍 Entités supportées](#-entités-supportées)
- [📊 Exemples avancés](#-exemples-avancés)
- [❗ Limitations](#-limitations)
- [📂 Structure du projet](#-structure-du-projet)
- [🤝 Contribution](#-contribution)
- [📝 Changelog](#-changelog)
- [🛡️ Licence](#️-licence)

---

## 🎯 Objectif

Fournir un pipeline fiable pour anonymiser automatiquement des documents `.docx`, `.xlsx`, `.csv`, `.txt` en remplaçant les entités sensibles (noms, lieux, dates, emails...) tout en respectant leur position dans le texte.

---

## 🚀 Fonctionnalités

| Fonction                 | Description |
|--------------------------|-------------|
| **Formats supportés**    | `.docx`, `.xlsx`, `.csv`, `.txt` |
| **NER spaCy**            | `PER`, `LOC`, `ORG`, `DATE`, `MISC` |
| **Détection e-mails**    | Via regex robuste |
| **Remplacement précis**  | Basé sur `start_char` / `end_char` pour éviter les erreurs |
| **Données factices**     | Faker `fr_FR` pour noms, lieux, dates, emails |
| **Filtrage d'entités**   | `--entities PER,LOC,EMAIL,...` |
| **Mode audit**           | `--dry-run` sans écriture |
| **Export d'entités**     | CSV/JSON via `--log-entities` |
| **GUI (alpha)**          | Interface simple multiplateforme |

---

## 💻 Prérequis

- Python ≥ 3.8 (recommandé : 3.11)
- pip
- Git
- Environnement virtuel (optionnel mais recommandé)

---

## ⚙️ Installation

```bash
git clone https://github.com/votre-orga/anonyfiles-cli.git
cd anonyfiles-cli

python3.11 -m venv .venv
source .venv/bin/activate     # macOS/Linux
.\.venv\Scriptsctivate      # Windows

pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

Pour utiliser la GUI :

```bash
pip install -r requirements-gui.txt
```

---

## 🛠️ Configuration

Créez un fichier `config.yaml` :

```yaml
spacy_model: fr_core_news_md
entities:
  - PER
  - LOC
  - ORG
  - DATE
  - EMAIL
output_dir: output_files
fake_data: true
log:
  format: csv
  path: log/entities.csv
```

---

## 💡 Utilisation

### CLI

```bash
python main.py anonymize <INPUT_FILE> [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Chemin du fichier de sortie |
| `-e, --entities` | Types d'entités à anonymiser |
| `-l, --log-entities` | Fichier CSV/JSON d'entités |
| `-n, --dry-run` | Pas d’écriture, juste analyse |
| `--fake-data / --redact` | Remplacer par Faker ou `[REDACTED]` |
| `--verbose` | Mode verbeux |
| `--gui` | Lancer l'interface graphique |

### GUI (alpha)

```bash
python main.py --gui
```

Dev (React + Tailwind + Rust Tauri) :

```bash
cd gui
npm install
npm run dev
```

Build final :

```bash
npm run build && tauri build
```

---

## 🔍 Entités supportées

| Code | Description | Source |
|------|-------------|--------|
| PER | Personne     | spaCy |
| LOC | Lieu         | spaCy |
| ORG | Organisation | spaCy |
| DATE| Date         | spaCy |
| MISC| Divers       | spaCy |
| EMAIL| Adresse mail| Regex |

---

## 📊 Exemples avancés

Lister les entités d’un modèle :

```bash
python main.py list-entities --model fr_core_news_md
```

Tester sans modifier les fichiers :

```bash
python main.py anonymize mon.docx --dry-run
```

Anonymiser un fichier TXT :

```bash
python main.py anonymize input.txt -e PER EMAIL --log-entities entites.csv
```

---

## ❗ Limitations

- Le formatage complexe `.docx` (gras, couleurs) est supprimé lors du remplacement.
- Certaines entités peuvent ne pas être détectées si mal orthographiées ou contextuelles.
- Pas encore de traitement batch natif ni de gestion PDF.

---

## 📂 Structure du projet

```
anonyfiles-cli/
├── main.py
├── requirements.txt
├── config.yaml.sample
├── anonymizer/
│   ├── anonymizer_core.py
│   ├── spacy_engine.py
│   ├── replacer.py
│   ├── word_processor.py
│   ├── excel_processor.py
│   ├── csv_processor.py
│   └── txt_processor.py
├── input_files/
├── output_files/
├── log/
└── gui/
    ├── src/
    ├── tauri.conf.json
    └── assets/
```

---

## 🤝 Contribution

1. Fork du repo
2. Créer une branche `feature/x`
3. Ajouter vos tests
4. Proposer une PR

---

## 📝 Changelog

- **v1.2.0** (2025‑05‑07) – GUI alpha, support YAML
- **v1.1.0** (2025‑04‑20) – Améliorations Excel/CSV
- **v1.0.0** (2025‑04‑10) – Release initiale

---

## 🛡️ Licence

MIT © 2025 Simon Grossi

---

## 🧭 Feuille de route (Roadmap)

### Phase 1 : Flexibilité et Robustesse de Base
- ✅ Gestion de la configuration via fichier YAML (modèle, entités, options)
- 🔜 Paramétrage de la stratégie de remplacement (`fake` vs `[REDACTED]`) dans `config.yaml`
- 🔜 Messages d’erreur plus clairs et journalisation améliorée (INFO, DEBUG, ERROR)

### Phase 2 : Qualité et Précision de la Sortie
- 🔜 Préservation du formatage des fichiers `.docx` (gras, couleurs, etc.)
- 🔜 Priorisation des entités détectées multiples (ex. EMAIL vs LOC)
- 🔜 Détection améliorée pour d’autres entités comme les numéros de téléphone

### Phase 3 : Performance et Scalabilité
- 🔜 Traitement mémoire efficace pour fichiers TXT et CSV (streaming/chunking)
- 🔜 Amélioration de la gestion de fichiers Excel/Word volumineux

### Phase 4 : Extension et Fonctionnalités Avancées
- 🔜 Refactorisation du cœur (`main.py` et `anonymizer_core.py`)
- 🔜 Support de nouveaux formats : PDF, JSON, XML
- 🔜 Stratégies d’anonymisation personnalisées (via config ou plugins Python)

### Phase 5 : Expérience Utilisateur
- 🔜 Barres de progression en CLI
- 🔜 Interface GUI complète (glisser-déposer, sélection entités, logs visuels)
- 🔜 Documentation complète via Sphinx ou MkDocs


---

## 🗂️ Détail de la structure du projet

```
anonyfiles-cli/
├── main.py                   # Point d'entrée CLI (typer)
├── requirements.txt          # Dépendances de base
├── requirements-gui.txt      # Dépendances GUI (React/Tauri)
├── config.yaml.sample        # Exemple de configuration
├── input_files/              # Fichiers à anonymiser
├── output_files/             # Résultats anonymisés
├── log/                      # Dossiers de logs d’entités
├── anonymizer/               # Cœur du traitement d’anonymisation
│   ├── anonymizer_core.py    # Fonctions de détection/remplacement avec offsets
│   ├── spacy_engine.py       # Initialisation SpaCy + détection + regex e-mails
│   ├── replacer.py           # Génération des remplacements avec Faker
│   ├── word_processor.py     # Traitement des fichiers Word (.docx)
│   ├── excel_processor.py    # Traitement des fichiers Excel (.xlsx)
│   ├── csv_processor.py      # Traitement des fichiers CSV (.csv)
│   └── txt_processor.py      # Traitement des fichiers texte (.txt)
└── gui/                      # Interface graphique (alpha)
    ├── src/                  # Code frontend (React/Tailwind ou Svelte)
    ├── tauri.conf.json       # Config Tauri
    └── assets/               # Ressources statiques (logos, styles, etc.)
```

Chaque module `*_processor.py` contient :
- Une fonction d’extraction de texte brut (pour analyse SpaCy).
- Une fonction de remplacement positionnel dans le fichier original.

`main.py` orchestre tout : lecture, détection, filtrage, remplacement, export.

