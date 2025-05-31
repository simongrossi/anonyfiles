# 🖥️ Anonyfiles CLI

**Anonyfiles CLI** est l’outil en ligne de commande du projet Anonyfiles pour anonymiser des fichiers texte, tableurs et documents Office. Il utilise le NLP (spaCy), une configuration flexible en YAML et plusieurs stratégies de remplacement, garantissant la confidentialité des données personnelles dans tous types de documents professionnels.

---

## 🚀 Fonctionnalités principales

* **Multi-format :** `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json` (avec gestion améliorée des fichiers vides).
* **Détection d’entités avancée** (spaCy) : Personnes (`PER`), Lieux (`LOC`), Organisations (`ORG`), Dates, Emails, Téléphones, IBAN, Adresses, etc.
* **Configuration YAML des stratégies spaCy** : personnalisation fine des stratégies de remplacement (Faker, codes, etc.) pour les entités *détectées par spaCy*, et exclusions par pattern.
* **Règles de remplacement personnalisées via CLI (pour .TXT initialement) :** Définissez vos propres patterns (texte ou regex simple) et leurs remplacements directs, appliqués *avant* la détection spaCy.
* **Export CSV du mapping d’anonymisation** : permet la désanonymisation/audit des entités traitées par spaCy.
* **Log CSV des entités détectées** (par spaCy) : suivi, validation, stats.
* **Exclusion sélective d’entités spaCy** via `--exclude-entities`.
* **Désanonymisation complète** via le mapping CSV généré.
* **Support du traitement batch de plusieurs fichiers** (par dossier).
* **Performance optimisée** pour les gros volumes (lazy loading, memory-safe).
* **Logs détaillés/debug** activables.

---

## 🛠️ Prérequis & Installation

* Python 3.8 ou supérieur
* Cloner le dépôt :
    ```sh
    git clone https://github.com/simongrossi/anonyfiles.git
    cd anonyfiles/anonyfiles_cli
    ```
* Installer les dépendances Python :
    ```sh
    pip install -r requirements.txt
    ```
* (Optionnel) Installer [spaCy FR](https://spacy.io/models/fr) :
    ```sh
    python -m spacy download fr_core_news_md
    ```

---

## 💡 Utilisation rapide

### ▶️ Anonymisation d’un fichier

```sh
python main.py anonymize chemin/vers/fichier.txt   --config chemin/vers/config.yaml   --custom-replacements-json '[{"pattern": "Mon Texte Secret", "replacement": "[REMPLACÉ]", "isRegex": false}]'   -o chemin/vers/fichier_anonymise.txt   --log-entities chemin/vers/log_entities.csv   --mapping-output chemin/vers/mapping.csv   --exclude-entities ORG,EMAIL,LOC
```

### 📌 Syntaxe CLI : résumé des options

- **Argument positionnel obligatoire :** chemin du fichier à anonymiser
- **Option `--config` obligatoire** : chemin vers le fichier YAML
- **Options facultatives les plus courantes :**
  - `--custom-replacements-json` : chaîne JSON sérialisée de règles `{pattern, replacement, isRegex}`
  - `--output-dir` : dossier de sortie (au lieu de `-o` fichier précis)
  - `--force` : écrase les fichiers existants
  - `--exclude-entities` : exclut certaines entités détectées par spaCy
  - `--has-header-opt true|false` : utile pour les fichiers CSV

### Exemple minimal d’appel CLI
```bash
python3 main.py anonymize   --config ./config.yaml   ./input_files/exemple.txt
```

---

## ✨ Utilisation des Règles de Remplacement Personnalisées (TXT uniquement)

En complément de l'anonymisation basée sur spaCy (configurée via YAML), vous pouvez fournir vos propres règles de recherche/remplacement directes via la ligne de commande. Ces règles sont appliquées **avant** l'analyse spaCy.

**Format JSON attendu** : liste d’objets `{pattern, replacement, isRegex}`

Exemple :
```bash
python main.py anonymize mon_fichier.txt   --config ma_config.yaml   --custom-replacements-json '[{"pattern": "CodeAlpha", "replacement": "[PROJET_X]", "isRegex": false}, {"pattern": "Réunion Marketing", "replacement": "[ÉVÉNEMENT_INTERNE]"}]'
```

> 💡 Cette chaîne JSON doit être encadrée par `'` dans le shell pour éviter des erreurs d’interprétation.

> ⚠️ Ces remplacements **ne sont pas tracés dans le fichier de mapping CSV global** (qui concerne uniquement les entités anonymisées par spaCy).

---

## 🔄 Désanonymisation (des entités spaCy)
```bash
python main.py deanonymize chemin/vers/fichier_anonymise.txt   --mapping-csv chemin/vers/mapping.csv   -o chemin/vers/fichier_restaure.txt
```

---

## 🧩 Exemple de configuration YAML (pour les stratégies d'entités spaCy)

```yaml
spacy_model: fr_core_news_md # Modèle spaCy à utiliser

replacements:
  PER:
    type: fake
    options:
      locale: fr_FR
  ORG:
    type: code
    options:
      prefix: ENTREPRISE_
      padding: 3 # Ex: ENTREPRISE_001
  EMAIL:
    type: redact
    options:
      text: "[EMAIL_CONFIDENTIEL]"
  DATE:
    type: placeholder
    options:
      format: "[DATE:{}]" # {} sera remplacé par le label de l'entité (DATE)

exclude_entities:
  # - ORG
  # - LOC
```

> 🎯 `exclude_entities` (dans le YAML) a le même effet que l'option CLI `--exclude-entities`, mais cette dernière est prioritaire.

---

## 📎 Option d'entête CSV

- `--has-header-opt true|false` indique si le fichier CSV a une ligne d'entête
- Exemple avec entête :
```bash
python main.py anonymize fichier.csv --config config.yaml --has-header-opt true
```

> ❓ Si cette option n’est pas renseignée, le système peut faire une détection automatique, mais il est préférable d’être explicite.

---

## 🔍 Table des entités supportées (par spaCy et stratégies YAML possibles)

| Type        | Label | Exemple                | Stratégie(s) YAML |
|-------------|-------|------------------------|--------------------|
| Personnes   | PER   | Jean Dupont            | fake, code, redact, placeholder |
| Lieux       | LOC   | Paris, Orléans         | fake, code, redact, placeholder |
| Organisations| ORG | ACME Corp.             | fake, code, redact, placeholder |
| Email       | EMAIL | contact@acme.fr        | fake, code, redact, placeholder |
| Dates       | DATE  | 2024-04-18             | fake, code, redact, placeholder |
| Téléphone   | PHONE | 0612345678             | fake, code, redact, placeholder |
| IBAN        | IBAN  | FR76...                | fake, code, redact, placeholder |
| Adresse     | ADDRESS| 12 rue X, 75000 Y     | fake, code, redact, placeholder |

> 🔎 Certains labels comme PHONE ou ADDRESS peuvent nécessiter un modèle `fr_core_news_lg` ou une détection personnalisée.

---

## 📂 Structure détaillée du projet

```
anonyfiles_cli/
├── main.py
├── requirements.txt
├── README.md
├── anonymizer/
│   ├── __init__.py
│   ├── anonyfiles_core.py
│   ├── spacy_engine.py
│   ├── replacer.py
│   ├── base_processor.py
│   ├── txt_processor.py
│   ├── csv_processor.py
│   ├── docx_processor.py
│   ├── excel_processor.py
│   ├── pdf_processor.py
│   ├── json_processor.py
│   ├── utils.py
│   └── deanonymize.py
├── config/
│   ├── config.yaml
│   ├── generated_config.yaml
│   └── schema.yaml
├── examples/
│   └── exemple.txt
├── output_files/
├── log/
├── mappings/
└── tests/
```

---

## 📝 Bonnes pratiques & conseils

- Sécurisez vos mappings ! Les fichiers de mapping CSV permettent la désanonymisation totale des entités spaCy.
- Testez sur des jeux de données non sensibles avant la mise en production.
- Documentez vos configurations YAML et conservez-les pour l’audit.
- Vérifiez régulièrement les logs d’entités spaCy pour contrôler les faux positifs/négatifs.
- Tenez à jour spaCy et Faker pour profiter des dernières améliorations.
- Pour les règles personnalisées via CLI, soyez précis avec vos patterns, surtout si vous utilisez des expressions régulières, pour éviter des remplacements non désirés.

---

## 📜 Licence
Distribué sous licence MIT.

## 💬 Ressources & liens utiles
- [Documentation complète (repo GitHub)](https://github.com/simongrossi/anonyfiles)
- [Anonyfiles GUI (interface graphique)](https://github.com/simongrossi/anonyfiles)
- [spaCy Documentation](https://spacy.io/)
- [Faker Documentation](https://faker.readthedocs.io/)
