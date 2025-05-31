# 🖥️ Anonyfiles CLI

**Anonyfiles CLI** est l’outil en ligne de commande du projet [Anonyfiles](https://github.com/simongrossi/anonyfiles), conçu pour **anonymiser et désanonymiser des documents texte, tableurs et fichiers bureautiques**.  
Il s’appuie sur le NLP (spaCy), une configuration flexible en YAML, et des règles personnalisables pour **garantir la confidentialité des données sensibles**.

---

## 🚀 Fonctionnalités principales

- **Multi-format** :
  - `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
  - Prise en charge des fichiers vides et fichiers à grand volume.

- **Détection automatique d’entités** avec **spaCy** :
  - Personnes (`PER`), Lieux (`LOC`), Organisations (`ORG`), Dates, Emails, Téléphones, IBAN, Adresses…

- **Configuration YAML** :
  - Définissez des stratégies spécifiques pour chaque type d'entité détectée (faker, code, masquage, placeholder…).
  - Activez/désactivez certains types d’entités.

- **Règles personnalisées supplémentaires** :
  - En plus de spaCy, vous pouvez injecter des règles simples de remplacement (texte ou regex) via la CLI, **appliquées en amont** du NLP.

- **Export de mapping** :
  - CSV traçant chaque entité remplacée automatiquement via spaCy.
  - Fichier de **log CSV** pour visualiser et auditer les remplacements.

- **Mode batch** :
  - Possibilité de traiter un dossier complet de fichiers.

- **Désanonymisation** :
  - Possibilité de restaurer les documents anonymisés à partir du mapping.

- **Robustesse et performance** :
  - Lazy loading, gestion mémoire efficace, journalisation détaillée, gestion fine des erreurs.

---

## 🛠️ Prérequis & Installation

### 📦 Dépendances techniques

- Python **3.8+**
- Pip et venv recommandés
- (Facultatif) : modèle spaCy français

### 🧪 Installation rapide

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles/anonyfiles_cli
pip install -r requirements.txt
python -m spacy download fr_core_news_md  # si ce n'est pas déjà fait
```
### 📁 Détail des dossiers & fichiers

- `main.py` : Point d'entrée principal de l'application CLI (anonymisation et désanonymisation).
- `requirements.txt` : Liste des dépendances Python requises pour exécuter le projet.
- `README.md` : Ce fichier, documentation complète de l’outil CLI.
- `anonymizer/` : Dossier contenant tout le cœur métier de l’anonymisation :
  - `anonyfiles_core.py` : Coordination globale (chargement, moteur, logique principale).
  - `spacy_engine.py` : Initialisation et exécution du moteur spaCy.
  - `replacer.py` : Application des stratégies de remplacement.
  - `base_processor.py` : Classe de base commune aux différents types de fichiers.
  - `txt_processor.py`, `csv_processor.py`, etc. : Traitements spécifiques à chaque format.
  - `utils.py` : Fonctions utilitaires (horodatage, nettoyage, etc.).
  - `audit.py` : Journalisation des entités détectées.
  - `deanonymize.py` : Fonction pour restaurer un fichier à partir d’un mapping CSV.
- `config/` : Fichiers de configuration YAML (exemples, schémas, modèles générés).
- `examples/` : Fichiers de test et démos simples.
- `output_files/` : Dossier de destination recommandé pour les fichiers anonymisés.
- `log/` : Dossier de log contenant les entités détectées (`--log-entities`).
- `mappings/` : Contient les fichiers CSV de correspondance générés (`--mapping-output`).
- `tests/` : Tests unitaires ou scripts de vérification (à compléter selon les cas).

---

## 💡 Utilisation rapide

### ▶️ Anonymisation d’un fichier

```bash
python main.py anonymize ./mon_fichier.txt   --config ./config.yaml   --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET]", "isRegex": false}]'   -o ./output/anonymise.txt   --log-entities ./log/entities.csv   --mapping-output ./mappings/mapping.csv   --exclude-entities ORG,EMAIL,LOC
```

### 📌 Options CLI résumées

| Option                         | Description |
|-------------------------------|-------------|
| `INPUT_FILE`                  | (obligatoire) Fichier à anonymiser |
| `--config`                    | (obligatoire) Chemin du fichier YAML |
| `--custom-replacements-json` | Règles simples de remplacement (JSON sérialisé) |
| `--output-dir` ou `-o`        | Fichier ou dossier de sortie |
| `--force`                     | Écrase les fichiers existants |
| `--exclude-entities`         | Entités spaCy à ignorer |
| `--log-entities`             | Export CSV des entités détectées |
| `--mapping-output`           | Export CSV des remplacements spaCy |
| `--has-header-opt true|false`| Indique si le CSV a une entête |

### Exemple minimal

```bash
python3 main.py anonymize --config ./config.yaml ./input/exemple.txt
```

---

## ✨ Règles personnalisées (pré-spaCy)

Ces règles sont **appliquées avant** le traitement spaCy.  
Format JSON attendu : `[{pattern, replacement, isRegex}]`

Exemple :

```bash
python main.py anonymize fichier.txt   --config config.yaml   --custom-replacements-json '[{"pattern": "Alpha123", "replacement": "[REMPLACÉ]"}]'
```

> ⚠️ Ces remplacements ne sont **pas inclus** dans le mapping CSV (car non générés par spaCy).

---

## 🔄 Désanonymisation

```bash
python main.py deanonymize fichier_anonymise.txt   --mapping-csv mappings/mapping.csv   -o fichier_restaure.txt
```

---

### 📂 Structure détaillée du projet

```
anonyfiles_cli/
├── main.py                          # Point d'entrée principal de la CLI (anonymize / deanonymize)
├── requirements.txt                # Dépendances Python nécessaires pour exécuter le projet
├── README.md                       # Documentation détaillée de l'outil CLI

├── anonymizer/                     # Dossier principal contenant le moteur d'anonymisation
│   ├── anonyfiles_core.py         # Orchestration centrale : charge la config, sélectionne les processeurs, exécute le pipeline
│   ├── spacy_engine.py            # Initialisation et exécution de spaCy pour la détection d'entités nommées
│   ├── replacer.py                # Applique les stratégies de remplacement définies dans le YAML
│   ├── base_processor.py          # Classe de base commune à tous les types de fichiers (héritage)
│   ├── txt_processor.py           # Traitement spécifique des fichiers .txt (ligne à ligne)
│   ├── csv_processor.py           # Traitement des fichiers .csv avec ou sans en-tête
│   ├── docx_processor.py          # Lecture et anonymisation des fichiers Word (.docx)
│   ├── excel_processor.py         # Traitement des fichiers Excel (.xlsx)
│   ├── pdf_processor.py           # Extraction de texte brute des fichiers PDF (via pdfplumber, PyMuPDF ou équivalent)
│   ├── json_processor.py          # Traitement récursif et anonymisation de fichiers JSON
│   ├── utils.py                   # Fonctions utilitaires (horodatage, création chemins, etc.)
│   ├── audit.py                   # Génère les logs CSV des entités détectées par spaCy
│   └── deanonymize.py            # Fonction de désanonymisation à partir du mapping CSV

├── config/                         # Fichiers de configuration
│   ├── config.yaml                # Exemple de configuration de remplacement par entité (modèle spaCy, stratégies…)
│   ├── generated_config.yaml      # Fichier généré dynamiquement ou modifié par interface/API
│   └── schema.yaml                # Schéma de validation YAML (à usage futur)

├── examples/                       # Fichiers de test ou de démonstration
│   └── exemple.txt                # Exemple simple pour tester l’anonymisation

├── output_files/                   # Dossier recommandé pour recevoir les fichiers anonymisés
├── log/                            # Dossier contenant les fichiers CSV de log des entités (via --log-entities)
├── mappings/                       # Dossier contenant les fichiers de correspondance anonymisation/désanonymisation (via --mapping-output)
└── tests/                          # Dossier réservé pour les tests unitaires (à compléter)
```
---

## 🧩 Exemple de fichier `config.yaml`

```yaml
spacy_model: fr_core_news_md

replacements:
  PER:
    type: fake
    options:
      locale: fr_FR
  ORG:
    type: code
    options:
      prefix: ORG_
      padding: 4
  EMAIL:
    type: redact
    options:
      text: "[EMAIL_CONFIDENTIEL]"
  DATE:
    type: placeholder
    options:
      format: "[DATE:{}]"

exclude_entities:
  # Exemple : - ORG
```

---

## 🔍 Entités supportées & stratégies disponibles

| Entité        | Label  | Exemple                  | Stratégies YAML disponibles |
|---------------|--------|--------------------------|-----------------------------|
| Personne      | `PER`  | Jean Dupont              | fake, code, redact, placeholder |
| Organisation  | `ORG`  | ACME Corp.               | fake, code, redact, placeholder |
| Lieu          | `LOC`  | Paris, Nantes            | fake, code, redact, placeholder |
| Email         | `EMAIL`| contact@domaine.com      | fake, code, redact, placeholder |
| Date          | `DATE` | 12/05/2023               | fake, code, redact, placeholder |
| Téléphone     | `PHONE`| 0612345678               | fake, code, redact, placeholder |
| IBAN          | `IBAN` | FR7612345678901234567890 | fake, code, redact, placeholder |
| Adresse       | `ADDRESS` | 10 rue Victor Hugo     | fake, code, redact, placeholder |

> 📌 Si certaines entités ne sont pas détectées avec `fr_core_news_md`, essayez `fr_core_news_lg`.

---

## 🧭 Conseils d’usage & limites actuelles

### ✅ Conseils d’usage

- Travailler d’abord avec des **données non sensibles** pour tester vos configurations.
- Organiser vos fichiers dans des répertoires clairs (`input_files`, `output_files`, `log`, `mappings`).
- Soyez **précis dans vos règles personnalisées**, surtout avec des expressions régulières.

### ⚠️ Limites connues / en cours d'exploration

- Pour l’instant, seuls les formats **TXT**, **CSV** et **JSON** ont été réellement testés.  
  Le support des fichiers **Word (.docx)** et **PDF** est prévu, mais encore en phase exploratoire.
- Les remplacements faits via `--custom-replacements-json` **ne sont pas enregistrés dans le mapping CSV**.
- La désanonymisation ne couvre pour l’instant **que les entités NLP (spaCy)**.
- Certaines entités nécessitent peut-être un **modèle spaCy plus puissant** (`fr_core_news_lg`) ou des ajustements manuels.
- Une **option de transparence dans la suppression des fichiers temporaires de job** est à prévoir (logs, fichiers intermédiaires…).

### 🔭 À venir / idées en cours

- Rendre traçables les remplacements manuels pour une désanonymisation complète.
- Générer dynamiquement des fichiers `config.yaml` à partir d’exemples.
- Ajouter un validateur interactif des règles personnalisées.

---

## 📜 Licence

Distribué sous licence **MIT**.

---

## 📚 Liens utiles

- [📦 Projet complet GitHub](https://github.com/simongrossi/anonyfiles)
- [🖼️ Interface graphique Anonyfiles GUI](https://github.com/simongrossi/anonyfiles)
- [📖 spaCy Docs](https://spacy.io/)
- [🎲 Faker Docs](https://faker.readthedocs.io/)