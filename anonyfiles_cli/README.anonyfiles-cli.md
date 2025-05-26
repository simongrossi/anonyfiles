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
python main.py anonymize chemin/vers/fichier.txt \
  --config chemin/vers/config.yaml \
  --custom-replacements-json '[{"pattern": "Mon Texte Secret", "replacement": "[REMPLACÉ]"}]' \
  -o chemin/vers/fichier_anonymise.txt \
  --log-entities chemin/vers/log_entities.csv \
  --mapping-output chemin/vers/mapping.csv \
  --exclude-entities ORG,EMAIL,LOC
Paramètres principaux :
chemin/vers/fichier.txt : fichier à anonymiser
--config : chemin du fichier de configuration YAML (pour les stratégies spaCy)
--custom-replacements-json : (Optionnel) Chaîne JSON de règles de remplacement personnalisées directes (ex: '[{"pattern": "texte_a_cacher", "replacement": "[CACHE]"}]'). Initialement pour les fichiers .txt.
-o ou --output : fichier de sortie anonymisé
--log-entities : CSV listant les entités spaCy détectées
--mapping-output : CSV pour la désanonymisation des entités spaCy
--exclude-entities : entités spaCy à NE PAS anonymiser (par label)
Seuls le fichier d’entrée et la config YAML sont obligatoires. Utilisez --exclude-entities pour cibler précisément ce que vous souhaitez que spaCy anonymise ou ignore. Les règles personnalisées via CLI offrent un contrôle supplémentaire avant l'intervention de spaCy.

✨ Utilisation des Règles de Remplacement Personnalisées (pour .TXT initialement)
En complément de l'anonymisation basée sur spaCy (configurée via YAML), vous pouvez fournir vos propres règles de recherche/remplacement directes via la ligne de commande. Ces règles sont appliquées avant l'analyse spaCy, ce qui est utile pour masquer des termes spécifiques métier, des codes internes, ou pour forcer un certain remplacement avant que spaCy n'intervienne.

Les règles sont passées via l'option --custom-replacements-json avec une chaîne au format JSON. Chaque règle est un objet avec une clé "pattern" (le texte ou l'expression régulière simple à rechercher, actuellement insensible à la casse) et une clé "replacement" (le texte de remplacement).

Exemple :
Pour remplacer "CodeAlpha" par "[PROJET_X]" et "Réunion Marketing" par "[ÉVÉNEMENT_INTERNE]" dans mon_fichier.txt :

Bash

python main.py anonymize mon_fichier.txt \
  --config ma_config.yaml \
  --custom-replacements-json '[{"pattern": "CodeAlpha", "replacement": "[PROJET_X]"}, {"pattern": "Réunion Marketing", "replacement": "[ÉVÉNEMENT_INTERNE]"}]'
Note importante :

Actuellement, cette fonctionnalité de remplacement personnalisé via CLI est pleinement testée et opérationnelle pour les fichiers .txt.
Les "patterns" sont traités par re.sub avec re.IGNORECASE. Faites attention à l'échappement des caractères spéciaux si vous utilisez des regex complexes dans le JSON passé en ligne de commande (surtout avec les guillemets et les barres obliques inverses, selon votre terminal).
Ces remplacements personnalisés ne sont pas tracés dans le fichier de mapping CSV global (qui concerne les entités anonymisées par les stratégies spaCy).
🔄 Désanonymisation (des entités spaCy)
Bash

python main.py deanonymize chemin/vers/fichier_anonymise.txt \
  --mapping-csv chemin/vers/mapping.csv \
  -o chemin/vers/fichier_restaure.txt
Paramètres :
chemin/vers/fichier_anonymise.txt : fichier anonymisé
--mapping-csv : mapping CSV généré lors de l'anonymisation par spaCy
-o : fichier restauré
🧩 Exemple de configuration YAML (pour les stratégies d'entités spaCy)
Le fichier de configuration YAML (--config) vous permet de définir comment les entités automatiquement détectées par spaCy (Personnes, Lieux, Organisations, etc.) doivent être anonymisées. Vous pouvez y spécifier des stratégies de remplacement (données factices, codes, caviardage) et des options pour chaque type d'entité.

YAML

# Contenu de config.yaml (exemple)
spacy_model: fr_core_news_md # Modèle spaCy à utiliser

replacements: # Stratégies de remplacement pour les entités détectées par spaCy
  PER:
    type: fake # Remplacer les personnes par des noms factices de la locale spécifiée
    options:
      locale: fr_FR
  ORG:
    type: code # Remplacer les organisations par un code séquentiel
    options:
      prefix: ENTREPRISE_
      padding: 3 # Ex: ENTREPRISE_001
  EMAIL:
    type: redact # Caviarder les emails avec un texte spécifique
    options:
      text: "[EMAIL_CONFIDENTIEL]"
  DATE:
    type: placeholder # Remplacer par un placeholder formaté
    options:
      format: "[DATE:{}]" # {} sera remplacé par le label de l'entité (DATE)

# Exclure certains labels d'entités spaCy de l'anonymisation
# (Prioritaire sur les définitions dans 'replacements')
exclude_entities:
  # - ORG # Exemple: ne pas anonymiser les organisations, même si une règle existe dans 'replacements'
  # - LOC
spacy_model : spécifie le modèle spaCy à charger (ex: fr_core_news_sm, fr_core_news_md).
replacements : définit la stratégie de remplacement (ex: fake, code, redact, placeholder) et les options associées pour chaque type d'entité standard (PER, LOC, ORG, DATE, EMAIL, etc.) détectée par spaCy.
exclude_entities (dans le YAML) : liste des labels d'entités spaCy (ex: PER, ORG) qui ne doivent pas être anonymisées, même si détectées et même si une règle de remplacement est définie pour elles. Ceci est différent de l'option CLI --exclude-entities qui a un effet similaire et est généralement prioritaire si les deux sont utilisés.
Plus d’exemples dans le dossier examples/.

🔍 Table des entités supportées (par spaCy et stratégies de base dans le YAML)
Type	Label	Exemple	Stratégie(s) YAML possibles
Personnes	PER	Jean Dupont	fake, code, redact, placeholder
Lieux	LOC	Paris, Orléans	fake, code, redact, placeholder
Organisations	ORG	ACME Corp.	fake, code, redact, placeholder
Email	EMAIL	contact@acme.fr	fake, code, redact, placeholder
Dates	DATE	2024-04-18	fake, code, redact, placeholder
Téléphone	PHONE	0612345678	fake, code, redact, placeholder
IBAN	IBAN	FR76...	fake, code, redact, placeholder
Adresse	ADDRESS	12 rue X, 75000 Y	fake, code, redact, placeholder
...	...	...	...

Exporter vers Sheets
Note : La détection native de PHONE, IBAN, ADDRESS peut nécessiter des modèles spaCy plus larges (comme fr_core_news_lg) ou des règles de détection personnalisées (non couvertes par l'exemple de configuration YAML simple ci-dessus, mais possibles via une section custom_rules plus avancée dans le YAML si votre schema.yaml le permet pour définir de nouvelles étiquettes).

📂 Structure détaillée du projet
Plaintext

anonyfiles_cli/
│
├── main.py                # Point d’entrée principal pour la CLI
├── requirements.txt       # Dépendances Python
├── README.md              # Ce fichier
│
├── anonymizer/            # Moteur principal d’anonymisation
│   ├── __init__.py
│   ├── anonyfiles_core.py # Logique d’anonymisation (orchestration)
│   ├── spacy_engine.py    # Interactions avec spaCy pour la détection
│   ├── replacer.py        # Logique de génération des remplacements (pour spaCy)
│   ├── base_processor.py  # Classe de base pour les processeurs de fichiers
│   ├── txt_processor.py   # Processeur pour les fichiers .txt
│   ├── csv_processor.py   # Processeur pour les fichiers .csv
│   ├── docx_processor.py  # Processeur pour les fichiers .docx
│   ├── excel_processor.py # Processeur pour les fichiers .xlsx
│   ├── pdf_processor.py   # Processeur pour les fichiers .pdf
│   ├── json_processor.py  # Processeur pour les fichiers .json
│   ├── utils.py           # Fonctions utilitaires (ex: apply_positional_replacements)
│   └── deanonymize.py     # Logique de désanonymisation
│
├── config/                # Exemples de configurations et schémas
│   ├── config.yaml        # Exemple de fichier de configuration principal
│   ├── generated_config.yaml # Peut-être une config générée par l'UI
│   └── schema.yaml        # Schéma de validation pour config.yaml
│
├── examples/              # Exemples de fichiers d'entrée
│   ├── exemple.txt
│   └── ...
│
├── output_files/          # (Par défaut, généré) Fichiers anonymisés
├── log/                   # (Par défaut, généré) Logs d’entités
├── mappings/              # (Par défaut, généré) Mappings pour désanonymisation
├── tests/                 # Jeux de tests unitaires/qualité
│   └── ...
└── ...
(Structure de projet indicative, adaptez selon votre organisation réelle).

📝 Bonnes pratiques & conseils
Sécurisez vos mappings ! Les fichiers de mapping CSV permettent la désanonymisation totale des entités spaCy.
Testez sur des jeux de données non sensibles avant la mise en production.
Documentez vos configurations YAML et conservez-les pour l’audit.
Vérifiez régulièrement les logs d’entités spaCy pour contrôler les faux positifs/négatifs.
Tenez à jour spaCy et Faker pour profiter des dernières améliorations.
Pour les règles personnalisées via CLI, soyez précis avec vos patterns, surtout si vous utilisez des expressions régulières, pour éviter des remplacements non désirés.
📜 Licence
Distribué sous licence MIT.

💬 Ressources & liens utiles
Documentation complète (Lien vers votre repo principal)
Anonyfiles GUI (interface graphique)
spaCy Documentation
Faker Documentation