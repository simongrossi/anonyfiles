
# **🖥️ Anonyfiles CLI**

**Anonyfiles CLI** est l’outil en ligne de commande du projet [Anonyfiles](https://github.com/simongrossi/anonyfiles), conçu pour **anonymiser et désanonymiser des documents texte, tableurs et fichiers bureautiques**.

Il repose sur la bibliothèque `anonyfiles_core`, laquelle contient tout le moteur d’anonymisation. La CLI n’est donc qu’une interface qui appelle ce cœur commun.
Le projet est composé de trois couches : `anonyfiles_core` (moteur), `anonyfiles_cli` (interface en ligne) et `anonyfiles_api` (service REST).

Il s’appuie sur le NLP (spaCy), une configuration flexible en YAML, et des règles personnalisables pour **garantir la confidentialité des données sensibles**.

## **🚀 Fonctionnalités principales**

* **Multi-format** :
  + .txt, .csv, .docx, .xlsx, .pdf, .json
  + Prise en charge des fichiers vides et volumineux
* **Détection automatique d’entités avec spaCy** :
  + Personnes (PER), Lieux (LOC), Organisations (ORG), Dates, Emails, Téléphones, IBAN, Adresses...
* **Configuration YAML flexible** :
  + Stratégies d’anonymisation par type d’entité : faker, code, masquage, placeholder...
  + Activation/désactivation de certains types d’entités
  + Support d'une configuration utilisateur par défaut (~/.anonyfiles/config.yaml)
* **Règles personnalisées supplémentaires** :
  + Règles simples de remplacement (texte ou regex) injectables en ligne de commande, **avant** le NLP
* **Export de mapping détaillé** :
  + CSV listant chaque entité remplacée automatiquement via spaCy
  + Fichiers de logs CSV pour audit
* **Mode batch** :
  + Traitement d’un dossier complet de fichiers (en cours de développement)
  + Barre de progression visuelle lors du traitement
* **Désanonymisation réversible** :
  + Restauration des fichiers à partir du mapping
* **Robustesse et performance** :
  + Chargement paresseux de spaCy, gestion fine des erreurs, cache en mémoire
  + Interface console enrichie (Rich)
  + Indicateur de progression lors de l'anonymisation
* **Gestion des jobs** :
  + Nettoyage et listage des fichiers de sortie des jobs pour une meilleure gestion de la confidentialité.

## **🛠️ Prérequis & Installation**

### **🛆 Dépendances techniques**

* Python **3.11+**
* pip et environnements virtuels recommandés
* Modèle spaCy fr\_core\_news\_md ou lg

### **🧪 Installation rapide**

git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
python -m pip install -e .
# Installer le modèle spaCy séparément après les dépendances
python -m spacy download fr\_core\_news\_md

## **📁 Structure du projet refactorisée**

Le projet anonyfiles\_cli est conçu de manière modulaire, avec une séparation claire des responsabilités.

### **À la racine :**

* main.py : point d’entrée pour python -m anonyfiles\_cli.main
* `pyproject.toml` (à la racine) : dépendances Python et entry point CLI
* README.md : documentation

### **anonymizer/**

* anonyfiles\_core.py : coordination du processus principal
* spacy\_engine.py : instanciation spaCy et regex
* replacer.py : remplacements d’entités selon config YAML
* \*\_processor.py : traitements spécifiques par type de fichier
* audit.py : export CSV des entités
* utils.py : outils divers
* deanonymize.py : lecture du mapping CSV pour restaurer

### **managers/**

* config\_manager.py : fusion config utilisateur / CLI / YAML
* path\_manager.py : gestion des chemins de sortie, mapping, logs
* validation\_manager.py : validation YAML (Cerberus)

### **ui/**

* console\_display.py : affichage console enrichi (Rich)
* interactive\_mode.py : préparation d'un mode CLI interactif

### **commands/**

* anonymize.py : Logique de la commande anonymize
* deanonymize.py : Logique de la commande deanonymize
* config.py : Logique de la commande config
* batch.py : Logique de la commande batch
* utils.py : Commandes utilitaires diverses
* clean\_job.py : Logique de la commande job (suppression et listage)

### **config/**

* config.yaml : exemple de config utilisateur
* generated\_config.yaml : généré par interface ou API
* schema.yaml : schéma de validation YAML

### **Sorties & tests :**

* anonyfiles\_outputs/ : Répertoire par défaut des sorties.
  + runs/ : Contient les sous-dossiers pour chaque job (ex: 20250605-122744/).
* log/ : logs CSV (peut être configuré dans anonyfiles\_outputs/runs/{job\_id}/)
* mappings/ : fichiers de correspondance (peut être configuré dans anonyfiles\_outputs/runs/{job\_id}/)
* examples/ : jeux de données
* tests/cli/ : tests unitaires

## **💡 Utilisation rapide**

### **▶️ Exemple simple d'anonymisation**

> **Note :** La commande `anonyfiles-cli` est disponible après l'installation du paquet via `pip install .` ou `pip install -e .`.

```bash
anonyfiles-cli anonymize anonyfiles_cli/input.txt
```

Le résultat affichera un Job ID (un timestamp) et le chemin vers les fichiers générés dans un sous-dossier de anonyfiles_outputs/runs/.

En interne, cette commande instancie le moteur partagé :

```python
from anonyfiles_core import AnonyfilesEngine

engine = AnonyfilesEngine(config_path)
engine.anonymize_file("input.txt")
```


### **▶️ Exemple avancé d'anonymisation**

```bash
anonyfiles-cli anonymize anonyfiles_cli/input.txt \
 --output-dir anonyfiles_cli/output_test \
 --config anonyfiles_core/config/config.yaml \
 --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]' \
 --log-entities anonyfiles_cli/log/log.csv \
 --mapping-output anonyfiles_cli/mappings/mapping.csv
```

> **Astuce pour le JSON :**
> * Sous Windows (CMD/PowerShell), échappez les guillemets internes : `"[{\"pattern\": ...}]"`
> * Ou utilisez un fichier contenant le JSON : `--custom-replacements-json @rules.json`

### **▶️ Utilisation du mode interactif**

Pour choisir dynamiquement les entités à anonymiser, utilisez `--interactive` :

```bash
anonyfiles-cli anonymize anonyfiles_cli/input.txt --interactive
```

La CLI affichera la liste des labels (PER, ORG, LOC, EMAIL, DATE, ...) et générera automatiquement l'argument `--exclude-entities` selon vos choix.

### **⚙️ Installation des complétions**

Pour activer l'autocomplétion de la CLI, exécutez :

```bash
anonyfiles-cli --install-completion bash   # pour Bash
anonyfiles-cli --install-completion zsh    # pour Zsh
anonyfiles-cli --install-completion fish   # pour Fish
```

Vous pouvez aussi obtenir le script directement :

```bash
anonyfiles-cli completion bash
```


## **🧹 Gestion des jobs (nettoyage et listage)**

La CLI d'Anonyfiles permet de gérer les fichiers générés par chaque opération (anonymisation, désanonymisation) en utilisant un Job ID unique (basé sur un timestamp). Ceci est essentiel pour la confidentialité des données et le nettoyage des fichiers temporaires.

### **▶️ Lister tous les jobs**

Pour voir la liste de tous les jobs disponibles dans le répertoire de sortie par défaut :

```bash
anonyfiles-cli job list
```

Si vos jobs sont stockés dans un répertoire différent, utilisez --output-dir :

```bash
anonyfiles-cli job list --output-dir /chemin/vers/mon/dossier/de/sorties
```

### **▶️ Supprimer un job spécifique**

Pour supprimer un job et tous ses fichiers générés (anonymisés, mapping, logs) :

```bash
anonyfiles-cli job delete <JOB_ID> --output-dir /chemin/absolut/vers/anonyfiles/
```

Exemple concret :

Si votre job ID est 20250605-122744 et que le chemin de votre projet est /home/debian/anonyfiles, la commande serait :

```bash
anonyfiles-cli job delete 20250605-122744 --output-dir /home/debian/anonyfiles
```

Vous serez invité à confirmer la suppression. Pour supprimer sans confirmation, ajoutez --force :

```bash
anonyfiles-cli job delete 20250605-122744 --output-dir /home/debian/anonyfiles --force
```

## **📊 Gestion et analyse des logs**

La CLI offre des outils dédiés pour consulter et gérer les journaux d'application (situés par défaut dans `logs/`).

### **▶️ Lister les logs**

Affiche la liste des fichiers de logs disponibles :

```bash
anonyfiles-cli logs list
```

### **▶️ Interface interactive (TUI)**

Lance une interface texte graphique (basée sur Textual) pour explorer les logs en temps réel, avec filtrage et coloration syntaxique :

```bash
anonyfiles-cli logs interactive
```

*   **Navigation** : Utilisez les flèches ou la souris pour sélectionner un fichier.
*   **Filtrage** : Saisissez une regex (ex: `ERROR|CRITICAL`) pour filtrer les lignes.
*   **Rechargement** : Bouton "Recharger" pour rafraîchir la vue.

### **▶️ Nettoyer les logs**

Supprime tous les fichiers de logs :

```bash
anonyfiles-cli logs clear
```

## **📌 Options CLI résumées**

| **Option** | **Description** |
| --- | --- |
| INPUT_FILE | Fichier à anonymiser |
| --config | Fichier YAML de configuration |
| --custom-replacements-json | Remplacements simples JSON (appliqués avant spaCy). Accepte une chaîne ou un fichier (@file.json). |
| --output / -o | Fichier de sortie anonymisé/désanonymisé |
| --output-dir | Dossier où écrire les fichiers de sortie par défaut (incluant les sous-dossiers runs/) |
| --force | Écrase les fichiers de sortie existants (pour anonymize) ou supprime sans confirmation (pour job delete) |
| --exclude-entities | Types d'entités spaCy à exclure (ex: PER,LOC) |
| --interactive / -i | Sélection interactive des entités à anonymiser |
| --log-entities | Export CSV des entités détectées et leurs labels |
| --mapping-output | Fichier CSV de mapping (original_text -> anonymized_code) |
| --has-header-opt | true ou false pour les fichiers CSV/XLSX (prioritaire sur --csv-no-header) |
| --csv-no-header | Indique que le fichier CSV d'entrée N'A PAS d'en-tête |
| --append-timestamp | Ajoute un horodatage aux noms des fichiers de sortie par défaut |
| --dry-run | Mode simulation : affiche les actions sans modifier les fichiers (fonctionne aussi pour `config create` et `config reset`) |
| job delete <JOB_ID> | Supprime un job spécifique et son répertoire. Nécessite --output-dir si non par défaut. |
| job list | Liste les IDs de tous les jobs. Nécessite --output-dir si non par défaut. |

## **✨ Règles personnalisées (avant spaCy)**

```bash
anonyfiles-cli anonymize fichier.txt \
 --config config.yaml \
 --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]'
```

⚠️ Ces remplacements ne sont **pas** inclus dans le mapping CSV.

## **🔄 Désanonymisation**

```bash
anonyfiles-cli deanonymize fichier_anonymise.txt \
 --mapping-csv anonyfiles_cli/mappings/mapping.csv \
 -o anonyfiles_cli/fichier_restaure.txt \
 --permissive
```

### **Validation d'un fichier de configuration**

```bash
anonyfiles-cli config validate-config mon_config.yaml
```

## **🧹 Exemple de fichier config.yaml**

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

## **🔍 Entités supportées & stratégies YAML**

| **Entité** | **Label** | **Exemple** | **Stratégies disponibles** |
| --- | --- | --- | --- |
| Personne | PER | Jean Dupont | faker, code, redact, placeholder |
| Organisation | ORG | ACME Corp. | faker, code, redact, placeholder |
| Lieu | LOC | Paris, Nantes | faker, code, redact, placeholder |
| Email | EMAIL | contact@domaine.com | faker, code, redact, placeholder |
| Date | DATE | 12/05/2023 | faker, code, redact, placeholder |
| Téléphone | PHONE | 0612345678 | faker, code, redact, placeholder |
| IBAN | IBAN | FR7612345678901234567890 | faker, code, redact, placeholder |
| Adresse | ADDRESS | 10 rue Victor Hugo | faker, code, redact, placeholder |

📌 Essayez fr_core_news_lg si certaines entités sont mal détectées.

## **🗌 Conseils d’usage & limites**

### **✅ Conseils**

* Tester avec des données non sensibles
* Organiser les répertoires : input_files, anonyfiles_outputs/, log/, mappings/
* Bien définir ses regex personnalisées
* Utiliser la commande `anonyfiles-cli` pour plus de simplicité

### **⚠️ Limites actuelles**

* PDF et DOCX peu testés (TXT, CSV, JSON OK)
* --custom-replacements-json non inclus dans le mapping CSV
* Désanonymisation uniquement sur entités NLP
* Certaines entités nécessitent fr\_core\_news\_lg

## **🔭 Roadmap / En cours**

* Audit des remplacements manuels
* Génération interactive d’un config.yaml
* Validateur de règles personnalisées
* Mode batch avec parallélisation
* Barre de progression
* Mode interactif CLI (choix entités)
* Amélioration de la gestion des erreurs et des messages de diagnostic

## **📜 Licence**

Distribué sous licence **MIT**.

## **📚 Liens utiles**

* [📦 Projet complet GitHub](https://github.com/simongrossi/anonyfiles)
* [🖼️ Interface graphique Anonyfiles GUI](https://github.com/simongrossi/anonyfiles)
* [📖 spaCy Docs](https://spacy.io/)
* [🎲 Faker Docs](https://faker.readthedocs.io/)
* [💎 Rich Docs](https://rich.readthedocs.io/)
