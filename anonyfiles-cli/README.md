# 🖥️ Anonyfiles CLI

**Anonyfiles CLI** est l’outil en ligne de commande du projet Anonyfiles pour anonymiser des fichiers texte, tableurs et documents Office. Il utilise le NLP (spaCy), une configuration flexible en YAML et plusieurs stratégies de remplacement, garantissant la confidentialité des données personnelles dans tous types de documents professionnels.

---

## 🚀 Fonctionnalités principales

* **Multi-format :** `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
* **Détection d’entités avancée** (spaCy) : Personnes (`PER`), Lieux (`LOC`), Organisations (`ORG`), Dates, Emails, Téléphones, IBAN, Adresses, etc.
* **Stratégies de remplacement configurables** : données factices (Faker), codes séquentiels, `[REDACTED]`, placeholders, etc.
* **Configuration YAML** : personnalisation fine (entités à anonymiser ou à ignorer, formats de remplacement, exclusions par pattern...)
* **Export CSV du mapping d’anonymisation** : permet la désanonymisation/audit
* **Log CSV des entités détectées** : suivi, validation, stats
* **Exclusion sélective d’entités** via `--exclude-entities`
* **Désanonymisation complète** via le mapping CSV généré
* **Support du traitement batch de plusieurs fichiers** (par dossier)
* **Performance optimisée** pour les gros volumes (lazy loading, memory-safe)
* **Logs détaillés/debug** activables

---

## 🛠️ Prérequis & Installation

* Python 3.8 ou supérieur
* Cloner le dépôt :

  ```sh
  git clone https://github.com/simongrossi/anonyfiles.git
  cd anonyfiles/anonyfiles-cli
  ```
* Installer les dépendances Python :

  ```sh
  pip install -r requirements.txt
  ```
* (Optionnel) Installer [spaCy FR](https://spacy.io/models/fr) :

  ```sh
  python -m spacy download fr_core_news_md
  ```

---

## 💡 Utilisation rapide

### ▶️ Anonymisation d’un fichier

```sh
python main.py anonymize chemin/vers/fichier.txt \
  --config chemin/vers/config.yaml \
  -o chemin/vers/fichier_anonymise.txt \
  --log-entities chemin/vers/log_entities.csv \
  --mapping-output chemin/vers/mapping.csv \
  --exclude-entities ORG,EMAIL,LOC
```

* **Paramètres principaux** :

  * `chemin/vers/fichier.txt` : fichier à anonymiser
  * `--config` : chemin du fichier de configuration YAML
  * `-o` ou `--output` : fichier de sortie anonymisé
  * `--log-entities` : CSV listant toutes les entités détectées
  * `--mapping-output` : CSV pour la désanonymisation
  * `--exclude-entities` : entités à NE PAS anonymiser (par label)

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

## 🧩 Exemple de configuration YAML

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
