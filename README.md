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
| **NOUVEAU : Remplacement PER** | **Remplacement des noms de personnes (PER) par codes séquentiels (NOMnnn)** |
| **NOUVEAU : Mapping PER**     | **Export de la table Nom Original -> Code pour désanonymisation** |

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
fake_data: true  # Note: Ce paramètre affecte les entités autres que PER
log:
  format: csv
  path: log/entities.csv
```

---

## 💡 Utilisation CLI

```bash
python main.py anonymize input.docx --config config.yaml
```

Anonymiser rapidement et efficacement des documents .docx, .xlsx, .csv, .txt en remplaçant les entités sensibles (noms, lieux, dates, emails...). Le processus de remplacement respecte la structure et la lisibilité des fichiers. Les noms de personnes (entités PER) sont maintenant remplacés par des codes uniques (NOMnnn), et une table de correspondance peut être exportée pour la désanonymisation.

### Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Chemin fichier de sortie |
| `-e, --entities` | Entités ciblées (ex: -e PER -e LOC). Anonymise tout par défaut. |
| `-l, --log-entities` | Fichier log des entités détectées au format CSV. |
| `--fake-data / --redact` | Mode de remplacement pour les entités autres que PER. |
| `--mapping-output` | Chemin fichier CSV pour la table PER -> NOMnnn. |
| `--dry-run` | Simulation sans écriture de fichiers. |
| `--verbose` | Logs détaillés (debug). |

---

### 🔁 Comportement spécifique pour les entités PER

Contrairement aux autres types d'entités qui sont remplacés par des données Faker synthétiques ou par [REDACTED], les entités de type PERSONNE (PER) détectées sont remplacées par un code séquentiel unique sous la forme NOMnnn (ex: NOM001, NOM002, NOM010, etc.). Chaque nom de personne unique dans l'ensemble du document recevra le même code consistant.

Pour retrouver les noms originaux à partir de ces codes, il est essentiel d'exporter la table de correspondance. Utilisez l'option `--mapping-output` pour spécifier le chemin du fichier CSV de sortie pour cette table. Si cette option n'est pas utilisée, un fichier de mapping est généré par défaut à côté du fichier anonymisé, nommé d'après ce dernier avec le suffixe `_mapping.csv`. Ce fichier CSV contient deux colonnes : "Code" et "Nom Original".

Exemple d'utilisation :

```bash
python main.py anonymize input_files/mon_rapport.docx --mapping-output ./rapport_codes_mapping.csv
```

---

## 🔍 Entités supportées

| Code | Type | Source | Note |
|------|------|--------|------|
| PER | Personne | spaCy | Remplacé par code séquentiel (NOMnnn) |
| LOC | Lieu | spaCy | Remplacé par fausse ville ou REDACTED |
| ORG | Organisation | spaCy | Remplacé par fausse organisation ou REDACTED |
| DATE | Date | spaCy | Remplacé par fausse date ou REDACTED |
| MISC | Divers | spaCy | Remplacé par REDACTED |
| EMAIL | Adresse email | Regex | Remplacé par faux email ou REDACTED |

---

## 🗂️ Structure du projet CLI

```
anonyfiles/
├── main.py                  ← Script principal de la CLI
├── requirements.txt         ← Dépendances Python
├── config.yaml.sample       ← Exemple de fichier de configuration
│
├── anonymizer/              ← Modules d'anonymisation
│   ├── anonymizer_core.py   ← Logique principale de remplacement
│   ├── spacy_engine.py      ← Moteur SpaCy + détection EMAIL
│   ├── replacer.py          ← Génération des remplacements (codes NOMnnn, Faker, etc.)
│   ├── word_processor.py    ← Traitement des fichiers Word (.docx)
│   ├── excel_processor.py   ← Traitement des fichiers Excel (.xlsx)
│   ├── csv_processor.py     ← Traitement des fichiers CSV
│   └── txt_processor.py     ← Traitement des fichiers texte brut
│
├── input_files/             ← Dossier pour les fichiers à anonymiser
├── output_files/            ← Dossier pour les fichiers anonymisés
├── log/                     ← Export CSV des entités détectées ou mapping PER
```

---

## 🖼️ Interface Graphique (GUI)

L'interface graphique de anonyfiles est développée avec React + Tailwind CSS pour le frontend et Tauri (Rust) pour le backend natif. Elle permet une utilisation intuitive avec glisser-déposer, sélection des entités à anonymiser, et configuration visuelle.

### 🧱 Structure du dossier

```
anonyfiles-gui/
├── src/ (React)
├── public/
├── dist/
├── package.json
├── vite.config.ts
├── src-tauri/
│   ├── src/
│   ├── tauri.conf.json
```

### 📦 Installation & Lancement

```bash
cd anonyfiles-gui
npm install
cargo install tauri-cli
npm run tauri dev
```

---

## 🧭 Feuille de route (Roadmap)

Phase 1 – Robustesse de base  
✅ Fichier config.yaml  
🔜 Gestion fine des erreurs et logs  

Phase 2 – Précision et rendu  
🔜 Préservation du formatage .docx  
🔜 Détection multi-entité (avec priorité)  

Phase 3 – Performance  
🔜 Streaming CSV/TXT  
🔜 Meilleure gestion mémoire  

Phase 4 – Extensibilité  
🔜 Support PDF / JSON  
🔜 Anonymisation personnalisée  

Phase 5 – UX  
🔜 Documentation Sphinx  
🔜 GUI complète et ergonomique  

---

## 🤝 Contribution

- Fork du repo
- Créer une branche feature/xxx
- Ajouter des tests
- Proposer une Pull Request

---

## 📝 Changelog

- v1.3.0 – Remplacement des entités PER par codes séquentiels (NOMnnn) et ajout de l'option `--mapping-output` pour exporter la table de correspondance Nom Original -> Code.
- v1.2.0 – GUI alpha, config YAML
- v1.1.0 – CSV/XLSX améliorés
- v1.0.0 – Première version

---

## 🛡️ Licence

MIT © 2025 Simon Grossi