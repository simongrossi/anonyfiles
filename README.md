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

| Fonction                   | Description |
|----------------------------|-------------|
| Formats supportés          | `.docx`, `.xlsx`, `.csv`, `.txt` |
| Détection NER              | SpaCy `fr_core_news_md` |
| Détection EMAIL            | Regex robuste intégrée |
| Remplacement positionnel   | Respect des offsets `start_char` / `end_char` |
| Données de remplacement    | Faker (fr_FR) ou `[REDACTED]` |
| Fichier config YAML        | Modèle, entités, options |
| Mode simulation (`--dry`)  | Analyse sans écrire |
| Export CSV/JSON            | Journalisation des entités détectées |
| Interface graphique (GUI)  | Drag & drop, sélection visuelle |

---

## 💻 Prérequis

- Python ≥ 3.8 (recommandé 3.11)
- pip
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

Créer un fichier `config.yaml` :

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

## 💡 Utilisation CLI

```bash
python main.py anonymize input.docx --config config.yaml
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Chemin fichier de sortie |
| `-e, --entities` | Entités ciblées |
| `-l, --log-entities` | Fichier log des entités |
| `--fake-data / --redact` | Mode de remplacement |
| `--dry-run` | Simulation sans écriture |
| `--verbose` | Logs détaillés |

---

## 🔍 Entités supportées

| Code | Type           | Source     |
|------|----------------|------------|
| PER  | Personne       | spaCy      |
| LOC  | Lieu           | spaCy      |
| ORG  | Organisation   | spaCy      |
| DATE | Date           | spaCy      |
| MISC | Divers         | spaCy      |
| EMAIL| Adresse email  | Regex      |

---

## 🗂️ Structure du projet CLI

```
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

L'interface graphique de `anonyfiles` est développée avec **React + Tailwind CSS** pour le frontend et **Tauri (Rust)** pour le backend natif. Elle permet une utilisation intuitive avec glisser-déposer, sélection des entités à anonymiser, et configuration visuelle.

### 🧱 Structure du dossier

```
anonyfiles-gui/
├── src/                    # Frontend React (TypeScript)
│   ├── App.tsx            # Point d'entrée principal
│   ├── components/        # Dropzone, ProgressBar, EntitySelector, etc.
│   ├── pages/             # Pages principales (Accueil, Résultat)
│   ├── styles/            # Fichiers CSS ou configuration Tailwind
│   ├── utils/             # Fonctions utilitaires
│   └── index.tsx          # Point d’entrée ReactDOM
│
├── public/                # Fichiers statiques (favicon, index.html, etc.)
├── dist/                  # Fichiers générés après build (ne pas versionner)
│
├── package.json           # Dépendances Node.js + scripts npm
├── vite.config.ts         # Configuration Vite (frontend)
├── README.md              # Documentation spécifique GUI
│
└── src-tauri/             # Backend Rust (Tauri)
    ├── src/
    │   └── main.rs        # Logique Rust, commandes Tauri
    ├── tauri.conf.json    # Configuration globale Tauri
    └── target/            # Artéfacts compilés (à ignorer)
```

### 📦 Installation & Lancement

```bash
cd anonyfiles-gui
npm install
cargo install tauri-cli
npm run tauri dev
```

### 🏗️ Build de production

```bash
npm run build && tauri build
```

> L’interface est encore en cours de développement (alpha).

---

## 🧭 Feuille de route (Roadmap)

### Phase 1 – Robustesse de base
- ✅ Fichier `config.yaml`
- 🔜 Gestion fine des erreurs et logs

### Phase 2 – Précision et rendu
- 🔜 Préservation du formatage `.docx`
- 🔜 Détection multi-entité (avec priorité)

### Phase 3 – Performance
- 🔜 Streaming CSV/TXT
- 🔜 Meilleure gestion mémoire

### Phase 4 – Extensibilité
- 🔜 Support PDF / JSON
- 🔜 Anonymisation personnalisée

### Phase 5 – UX
- 🔜 Documentation Sphinx
- 🔜 GUI complète et ergonomique

---

## 🤝 Contribution

1. Fork du repo
2. Créer une branche `feature/xxx`
3. Ajouter des tests
4. Proposer une Pull Request

---

## 📝 Changelog

- **v1.2.0** – GUI alpha, config YAML
- **v1.1.0** – CSV/XLSX améliorés
- **v1.0.0** – Première version

---

## 🛡️ Licence

MIT © 2025 Simon Grossi
