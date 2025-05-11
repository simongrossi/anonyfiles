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

Anonymise le fichier spécifié en détectant et remplaçant les entités sensibles selon les règles définies dans le fichier de configuration ou les options CLI. Le processus de remplacement respecte la structure et la lisibilité des fichiers.

Le comportement de remplacement (codes séquentiels, données Faker, texte fixe, placeholder) est **entièrement configurable par type d'entité** via le fichier YAML.

### Options principales :

| Option                | Description |
|-----------------------|-------------|
| `--config PATH`       | Chemin vers le fichier de configuration YAML. Si non spécifié, utilise la configuration par défaut. |
| `-o, --output`        | Chemin du fichier de sortie. Prioritaire sur la valeur `output_dir` du fichier config. |
| `-l, --log-entities`  | Fichier CSV des entités détectées. Prioritaire sur `log.path` du fichier config. |
| `--mapping-output`    | Fichier CSV pour la table de correspondance Nom original → Code. Généré uniquement si des codes sont utilisés. |
| `--dry-run`           | Simule le traitement sans écrire de fichiers de sortie. |
| `--verbose`           | Affiche les logs détaillés (mode debug). |

---

### 🔁 Règles de remplacement :

Le type de remplacement appliqué à chaque entité détectée dépend de la règle définie dans la section `replacements` du fichier YAML :

- `type: codes` → Génère un code séquentiel unique (ex. NOM001)
- `type: faker` → Données factices réalistes avec Faker
- `type: redact` → Texte fixe (ex. [REDACTED])
- `type: placeholder` → Placeholder formaté avec le label (ex. `[PER]`)

Sans règle définie pour une entité : `[REDACTED]` est utilisé.

Les remplacements sont **cohérents** au sein d’un même fichier : une même entité est toujours remplacée par la même valeur.

---

### 📌 Exemples d'utilisation

```bash
# Anonymiser un fichier Word avec config personnalisée
python main.py anonymize input_files/mon_rapport.docx --config config.yaml

# Anonymiser un CSV avec simulation (dry-run) et log CSV des entités
python main.py anonymize input_files/clients.csv --log-entities log/entites.csv --dry-run

# Anonymiser un Excel avec export de la table de mapping des noms codés
python main.py anonymize input_files/donnees.xlsx --config config.yaml --mapping-output log/mapping_personnes.csv

# Utiliser la configuration intégrée par défaut (sans fichier config)
python main.py anonymize input_files/test.txt

# Liste des entités détectables par le modèle spaCy
python main.py list-entities --model fr_core_news_md
```


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

### Phase 1 – Robustesse de base
- ✅ Fichier `config.yaml` (pour la configuration des remplacements et des entités)
- 🔜 Gestion fine des erreurs et logs

### Phase 2 – Précision et rendu
- 🔜 Préservation du formatage `.docx`
- 🔜 Détection multi-entité (avec priorité)

### Phase 3 – Performance
- 🔜 Streaming CSV/TXT
- 🔜 Meilleure gestion mémoire
**(Ces deux points correspondent à la priorité #4 "Performance et gestion mémoire")**

### Phase 4 – Extensibilité
- 🔜 Support PDF / JSON
- 🔜 Anonymisation personnalisée (déjà partiellement couverte par la config YAML)
- 🔜 **Fonctionnalité de Désanonymisation** (ajout d'une commande CLI pour inverser l'anonymisation des codes via fichier mapping)
**(Ce point correspond à la priorité #7 "Fonctionnalité de Désanonymisation")**

### Phase 5 – UX
- 🔜 Documentation Sphinx
- 🔜 GUI complète et ergonomique

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
