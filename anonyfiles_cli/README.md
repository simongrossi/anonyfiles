# 🖥️ Anonyfiles CLI

**Anonyfiles CLI** est l’outil en ligne de commande du projet [Anonyfiles](https://github.com/simongrossi/anonyfiles), conçu pour **anonymiser et désanonymiser des documents texte, tableurs et fichiers bureautiques**.

Il s’appuie sur le NLP (spaCy), une configuration flexible en YAML, et des règles personnalisables pour **garantir la confidentialité des données sensibles**.

---

## 🚀 Fonctionnalités principales

* **Multi-format** :

  * `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
  * Prise en charge des fichiers vides et volumineux

* **Détection automatique d’entités avec spaCy** :

  * Personnes (`PER`), Lieux (`LOC`), Organisations (`ORG`), Dates, Emails, Téléphones, IBAN, Adresses...

* **Configuration YAML flexible** :

  * Stratégies d’anonymisation par type d’entité : faker, code, masquage, placeholder...
  * Activation/désactivation de certains types d’entités
  * Support d'une configuration utilisateur par défaut (`~/.anonyfiles/config.yaml`)

* **Règles personnalisées supplémentaires** :

  * Règles simples de remplacement (texte ou regex) injectables en ligne de commande, **avant** le NLP

* **Export de mapping détaillé** :

  * CSV listant chaque entité remplacée automatiquement via spaCy
  * Fichiers de logs CSV pour audit

* **Mode batch** *(bientôt)* :

  * Traitement d’un dossier complet de fichiers

* **Désanonymisation réversible** :

  * Restauration des fichiers à partir du mapping

* **Robustesse et performance** :

  * Chargement paresseux de spaCy, gestion fine des erreurs, cache en mémoire
  * Interface console enrichie (Rich)

---

## 🛠️ Prérequis & Installation

### 🛆 Dépendances techniques

* Python **3.8+**
* `pip` et environnements virtuels recommandés
* Modèle spaCy `fr_core_news_md` ou `lg`

### 🧪 Installation rapide

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles/anonyfiles_cli
pip install -r requirements.txt
pip install cerberus
python -m spacy download fr_core_news_md
```

---

## 📁 Structure du projet refactorisée

Le projet `anonyfiles_cli` est conçu de manière modulaire, avec une séparation claire des responsabilités.

### À la racine :

* `main.py` : point d’entrée pour `python -m anonyfiles_cli.main`
* `requirements.txt` : dépendances Python
* `README.md` : documentation

### `anonymizer/`

* `anonyfiles_core.py` : coordination du processus principal
* `spacy_engine.py` : instanciation spaCy et regex
* `replacer.py` : remplacements d’entités selon config YAML
* `*_processor.py` : traitements spécifiques par type de fichier
* `audit.py` : export CSV des entités
* `utils.py` : outils divers
* `deanonymize.py` : lecture du mapping CSV pour restaurer

### `managers/`

* `config_manager.py` : fusion config utilisateur / CLI / YAML
* `path_manager.py` : gestion des chemins de sortie, mapping, logs
* `validation_manager.py` : validation YAML (Cerberus)

### `ui/`

* `console_display.py` : affichage console enrichi (Rich)
* `interactive_mode.py` : préparation d'un mode CLI interactif

### `config/`

* `config.yaml` : exemple de config utilisateur
* `generated_config.yaml` : généré par interface ou API
* `schema.yaml` : schéma de validation YAML

### Sorties & tests :

* `output_files/` : fichiers anonymisés
* `log/` : logs CSV
* `mappings/` : fichiers de correspondance
* `examples/` : jeux de données
* `tests/` : tests unitaires à compléter

---

## 💡 Utilisation rapide

### ▶️ Exemple simple

```bash
python -m anonyfiles_cli.main anonymize anonyfiles_cli/input.txt
```

### ▶️ Exemple avancé

```bash
python -m anonyfiles_cli.main anonymize anonyfiles_cli/input.txt \
  --output-dir anonyfiles_cli/output_test \
  --config anonyfiles_cli/config/config.yaml \
  --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]' \
  --log-entities anonyfiles_cli/log/log.csv \
  --mapping-output anonyfiles_cli/mappings/mapping.csv
```

---

## 📌 Options CLI résumées

| Option                       | Description                   |
| ---------------------------- | ----------------------------- |
| `INPUT_FILE`                 | Fichier à anonymiser          |
| `--config`                   | Fichier YAML de configuration |
| `--custom-replacements-json` | Remplacements simples JSON    |
| `--output` / `-o`            | Fichier de sortie             |
| `--output-dir`               | Dossier de sortie             |
| `--force`                    | Écrase les fichiers           |
| `--exclude-entities`         | Entités spaCy à exclure       |
| `--log-entities`             | Export CSV d’audit            |
| `--mapping-output`           | Fichier CSV de mapping        |
| `--has-header-opt`           | `true` ou `false` pour CSV    |
| `--csv-no-header`            | CSV sans en-tête              |
| `--append-timestamp`         | Ajoute un horodatage          |
| `--dry-run`                  | Mode simulation               |

---

## ✨ Règles personnalisées (avant spaCy)

```bash
python -m anonyfiles_cli.main anonymize fichier.txt \
  --config config.yaml \
  --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]'
```

> ⚠️ Ces remplacements ne sont **pas** inclus dans le mapping CSV.

---

## 🔄 Désanonymisation

```bash
python -m anonyfiles_cli.main deanonymize fichier_anonymise.txt \
  --mapping-csv anonyfiles_cli/mappings/mapping.csv \
  -o anonyfiles_cli/fichier_restaure.txt \
  --permissive
```

---

## 🧹 Exemple de fichier `config.yaml`

```yaml
spacy_model: fr_core_news_md
replacements:
  PER:
    type: faker
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
  - ORG
```

---

## 🔍 Entités supportées & stratégies YAML

| Entité       | Label     | Exemple                                           | Stratégies disponibles           |
| ------------ | --------- | ------------------------------------------------- | -------------------------------- |
| Personne     | `PER`     | Jean Dupont                                       | faker, code, redact, placeholder |
| Organisation | `ORG`     | ACME Corp.                                        | faker, code, redact, placeholder |
| Lieu         | `LOC`     | Paris, Nantes                                     | faker, code, redact, placeholder |
| Email        | `EMAIL`   | [contact@domaine.com](mailto:contact@domaine.com) | faker, code, redact, placeholder |
| Date         | `DATE`    | 12/05/2023                                        | faker, code, redact, placeholder |
| Téléphone    | `PHONE`   | 0612345678                                        | faker, code, redact, placeholder |
| IBAN         | `IBAN`    | FR7612345678901234567890                          | faker, code, redact, placeholder |
| Adresse      | `ADDRESS` | 10 rue Victor Hugo                                | faker, code, redact, placeholder |

> 📌 Essayez `fr_core_news_lg` si certaines entités sont mal détectées.

---

## 🗌 Conseils d’usage & limites

### ✅ Conseils

* Tester avec des données non sensibles
* Organiser les répertoires : `input_files`, `output_files`, `log`, `mappings`
* Bien définir ses regex personnalisées
* Lancer depuis la racine avec `python -m anonyfiles_cli.main`

### ⚠️ Limites actuelles

* PDF et DOCX peu testés (TXT, CSV, JSON OK)
* `--custom-replacements-json` non inclus dans le mapping CSV
* Désanonymisation uniquement sur entités NLP
* Certaines entités nécessitent `fr_core_news_lg`
* Pas encore de nettoyage auto des fichiers temporaires

---

## 🔭 Roadmap / En cours

* Audit des remplacements manuels
* Génération interactive d’un `config.yaml`
* Validateur de règles personnalisées
* Mode batch avec parallélisation
* Barre de progression
* Mode interactif CLI (choix entités)

---

## 📜 Licence

Distribué sous licence **MIT**.

---

## 📚 Liens utiles

- [📦 Projet complet GitHub](https://github.com/simongrossi/anonyfiles)
- [🖼️ Interface graphique Anonyfiles GUI](https://github.com/simongrossi/anonyfiles)
- [📖 spaCy Docs](https://spacy.io/)
- [🎲 Faker Docs](https://faker.readthedocs.io/)
- [💎 Rich Docs](https://rich.readthedocs.io/)
