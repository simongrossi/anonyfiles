# 3. README CLI (`anonyfiles-cli/README.md`)

```markdown
# 🖥️ Anonyfiles CLI

**Anonyfiles CLI** est l’outil en ligne de commande pour anonymiser fichiers texte, tableurs et documents Office,  
en exploitant le NLP (spaCy), la configuration YAML et de multiples stratégies de remplacement.

---

## 🚀 Fonctionnalités principales

- Support : `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
- Détection entités via spaCy : Noms (PER), Lieux (LOC), Organisations (ORG), Dates, Emails, etc.
- Remplacement configurable (factice, codes, [REDACTED], etc.) via YAML
- Export mapping anonymisation (CSV) pour désanonymisation/relecture
- Log CSV des entités détectées
- Exclusion sélective d’entités via `--exclude-entities`
- Désanonymisation complète via mapping CSV

---

## 🛠️ Prérequis & Installation

- Python 3.8+
- pip install -r requirements.txt

---

## 💡 Utilisation

### Anonymisation d’un fichier

```sh
python main.py anonymize chemin/vers/fichier.txt \
  --config generated_config.yaml \
  -o chemin/vers/fichier_anonymise.txt \
  --log-entities chemin/vers/log_entities.csv \
  --mapping-output chemin/vers/mapping.csv \
  --exclude-entities ORG,EMAIL,LOC
Tous les paramètres sont optionnels sauf le fichier d’entrée et la config YAML.

Pour n’anonymiser qu’un type d’entité : passer --exclude-entities pour tout le reste.

Désanonymisation
sh
Copier
Modifier
python main.py deanonymize chemin/vers/fichier_anonymise.txt \
  --mapping-csv chemin/vers/mapping.csv \
  -o chemin/vers/fichier_restaure.txt
🧩 Configuration YAML
La configuration YAML permet de :

Spécifier les types d’entités à remplacer, ignorer, personnaliser le format

Définir les stratégies de remplacement pour chaque type

(Voir exemples de YAML dans le repo)

🔍 Exemples d’entités supportées
Type	Label
Personnes	PER
Lieux	LOC
Org.	ORG
Email	EMAIL
Dates	DATE
…	...

📜 Licence
MIT