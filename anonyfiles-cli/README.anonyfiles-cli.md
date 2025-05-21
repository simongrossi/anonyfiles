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
    git clone [https://github.com/simongrossi/anonyfiles.git](https://github.com/simongrossi/anonyfiles.git)
    cd anonyfiles/anonyfiles-cli
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
python main.py anonymize chemin/vers/fichier.txt \
  --config chemin/vers/config.yaml \
  --custom-replacements-json '[{"pattern": "Mon Texte Secret", "replacement": "[REMPLACÉ]"}]' \
  -o chemin/vers/fichier_anonymise.txt \
  --log-entities chemin/vers/log_entities.csv \
  --mapping-output chemin/vers/mapping.csv \
  --exclude-entities ORG,EMAIL,LOC
```

* **Paramètres principaux** :
  * `chemin/vers/fichier.txt` : fichier à anonymiser
  * `--config` : chemin du fichier de configuration YAML
  * `--custom-replacements-json` : (Optionnel) Chaîne JSON de règles de remplacement personnalisées (ex: `'[{"pattern": "texte_a_cacher", "replacement": "[CACHE]"}]'`). **Initialement pour les fichiers .txt.**
  * `-o` ou `--output` : fichier de sortie anonymisé
  * `--log-entities` : CSV listant les entités spaCy détectées
  * `--mapping-output` : CSV pour la désanonymisation des entités spaCy
  * `--exclude-entities` : entités spaCy à NE PAS anonymiser (par label)

> Seuls le fichier d’entrée et la config YAML sont obligatoires. Utilisez `--exclude-entities` pour cibler précisément ce que vous souhaitez anonymiser.

### 🔄 Désanonymisation

```sh
python main.py deanonymize chemin/vers/fichier_anonymise.txt \
  --mapping-csv chemin/vers/mapping.csv \
  -o chemin/vers/fichier_restaure.txt
```

* **Paramètres** :

  * `chemin/vers/fichier_anonymise.txt` : fichier anonymisé
  * `--mapping-csv` : mapping généré à l’anonymisation
  * `-o` : fichier restauré

---

### 🧩 Exemple de configuration YAML (pour les entités spaCy)

Le fichier de configuration YAML (`--config`) vous permet de définir comment les entités *automatiquement détectées par spaCy* (Personnes, Lieux, Organisations, etc.) doivent être anonymisées. Vous pouvez y spécifier des stratégies de remplacement (données factices, codes, caviardage) et des options pour chaque type d'entité.

**Note :** Pour des remplacements directs de chaînes de caractères ou de patterns spécifiques *avant* l'intervention de spaCy (actuellement pour les fichiers `.txt`), utilisez l'option en ligne de commande `--custom-replacements-json` (voir section "Utilisation rapide").

```yaml
entities:
  PER:
    strategy: fake
    faker_type: name
  ORG:
    strategy: code
    prefix: ORG
  EMAIL:
    strategy: redact
    placeholder: [REDACTED]
exclude_patterns:
  - "@example.com"
custom_rules:
  - pattern: "\d{10}"
    label: PHONE
    strategy: code
    prefix: TEL
```

* **entities** : pour chaque type d’entité, définir la stratégie de remplacement
* **exclude\_patterns** : patterns regex à ignorer
* **custom\_rules** : ajout de détection personnalisée (ex : numéros de téléphone)

Plus d’exemples dans le dossier [`examples/`](./examples/).

---

## 🔍 Table des entités supportées

| Type          | Label   | Exemple                                   | Stratégie(s)       |
| ------------- | ------- | ----------------------------------------- | ------------------ |
| Personnes     | PER     | Jean Dupont                               | fake, code, redact |
| Lieux         | LOC     | Paris, Orléans                            | fake, code, redact |
| Organisations | ORG     | ACME Corp.                                | fake, code, redact |
| Email         | EMAIL   | [contact@acme.fr](mailto:contact@acme.fr) | fake, code, redact |
| Dates         | DATE    | 2024-04-18                                | fake, code, redact |
| Téléphone     | PHONE   | 0612345678                                | fake, code, redact |
| IBAN          | IBAN    | FR76...                                   | fake, code, redact |
| Adresse       | ADDRESS | 12 rue X, 75000 Y                         | fake, code, redact |
| ...           | ...     | ...                                       | ...                |


---


### ✨ Utilisation des Règles de Remplacement Personnalisées (pour .TXT)

Vous pouvez fournir vos propres règles de recherche/remplacement qui seront appliquées *avant* l'analyse spaCy. Ceci est utile pour masquer des termes spécifiques métier, des codes internes, ou pour forcer un certain remplacement avant que spaCy n'intervienne.

Les règles sont passées via l'option `--custom-replacements-json` avec une chaîne au format JSON. Chaque règle est un objet avec une clé `"pattern"` (le texte ou l'expression régulière simple à rechercher, insensible à la casse) et une clé `"replacement"` (le texte de remplacement).

**Exemple :**
Pour remplacer "CodeAlpha" par "[PROJET_X]" et "Réunion Marketing" par "[ÉVÉNEMENT_INTERNE]" :

```sh
python main.py anonymize mon_fichier.txt \
  --config ma_config.yaml \
  --custom-replacements-json '[{"pattern": "CodeAlpha", "replacement": "[PROJET_X]"}, {"pattern": "Réunion Marketing", "replacement": "[ÉVÉNEMENT_INTERNE]"}]'


---

## 📂 Structure détaillée du projet

```
anonyfiles-cli/
│
├── main.py                # Point d’entrée principal pour la CLI
├── requirements.txt       # Dépendances Python
├── README.md              # Ce fichier
│
├── anonymizer/            # Moteur principal d’anonymisation
│   ├── __init__.py
│   ├── core.py            # Logique d’anonymisation (NER, remplacement, etc.)
│   ├── config.py          # Parsing/validation YAML
│   ├── mapping.py         # Mapping anonymisation <-> désanonymisation
│   ├── csv_utils.py       # Fonctions CSV (logs, mapping, batch)
│   ├── deanonymize.py     # Désanonymisation
│   └── ...
│
├── examples/              # Exemples de fichiers et configs YAML
│   ├── exemple.txt
│   ├── exemple.csv
│   ├── exemple.docx
│   ├── config_sample.yaml
│   └── ...
│
├── output_files/          # (Généré) Fichiers anonymisés
├── log/                   # (Généré) Logs d’entités
├── mappings/              # (Généré) Mappings pour désanonymisation
├── tests/                 # Jeux de tests unitaires/qualité
│   ├── test_core.py
│   └── ...
└── ...
```

---

## 📝 Bonnes pratiques & conseils

* **Sécurisez vos mappings !** Les fichiers de mapping CSV permettent la désanonymisation totale.
* **Testez sur des jeux de données non sensibles** avant la mise en production.
* **Documentez vos configs YAML** et conservez-les pour l’audit.
* **Vérifiez régulièrement les logs d’entités** pour contrôler les faux positifs/négatifs.
* **Tenez à jour spaCy et Faker** pour profiter des dernières améliorations.

---

## 📜 Licence

Distribué sous licence MIT.

---

## 💬 Ressources & liens utiles

* [Documentation complète](https://github.com/simongrossi/anonyfiles)
* [Anonyfiles GUI (interface graphique)](https://github.com/simongrossi/anonyfiles/tree/main/anonyfiles-gui)
* [spaCy Documentation](https://spacy.io/)
* [Faker Documentation](https://faker.readthedocs.io/)

---
