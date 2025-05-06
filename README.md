# 🕵️ anonyfiles

**anonyfiles** est un outil open source d’anonymisation de documents, basé sur `spaCy`. Il prend en charge les formats Word, Excel, CSV et TXT.

## ⚠️ Statut du projet

**anonyfiles est actuellement en phase de test.**  
Des bugs peuvent subsister et certaines fonctionnalités sont encore en cours de validation ou d'amélioration.  
Merci de faire preuve de vigilance et de ne pas l’utiliser sur des documents sensibles en production sans vérification.


## ⚙️ Fonctionnalités principales

- 📄 Support des fichiers `.docx`, `.xlsx`, `.csv`, `.txt`
- 🤖 Détection d'entités nommées (NER) avec spaCy (`fr_core_news_md`)
- 🧠 Génération automatique de remplacements fictifs avec `Faker`
- 🔐 Remplacement contextuel des noms, lieux, organisations, dates, etc.
- 📝 Export optionnel des entités détectées (`--log-entities`)
- 🎯 Filtrage des types d'entités à anonymiser (`--entities`)
- 📂 Traitement ligne par ligne ou global selon le format
- 💾 Fichiers de sortie conservant l'intégrité de la structure

---

## 🚀 Utilisation

```bash
python main.py input_files/mon_fichier.docx
```

### Avec export des entités détectées :
```bash
python main.py mon_fichier.docx --log-entities log/entites.csv
```

### Avec sélection des types d'entités à anonymiser :
```bash
python main.py mon_fichier.docx --entities PER ORG
```

---


## 📝 Export CSV des entités détectées

Vous pouvez ajouter `--log-entities fichier.csv` pour exporter toutes les entités détectées dans un fichier CSV.

Exemple :
```bash
python main.py fichier.docx --log-entities log/entites.csv
```

Ce fichier contiendra deux colonnes :
- **Entite** : le texte trouvé dans le document
- **Label** : son type (ex. `PER`, `LOC`, `ORG`, etc.)


## 🔧 Choix des entités à anonymiser

Par défaut, le script anonymise toutes les entités détectées par spaCy.  
Vous pouvez filtrer les types d'entités que vous souhaitez anonymiser à l'aide de l'option `--entities`.

**Exemple : anonymiser uniquement les personnes (PER) et les organisations (ORG)**

```bash
python main.py mon_fichier.docx --entities PER ORG
```

### Types d'entités courants (`fr_core_news_md`) :
- `PER` : Personnes (noms, prénoms)
- `LOC` : Lieux
- `ORG` : Organisations
- `DATE` : Dates
- `MISC` : Autres entités diverses

---


---

## 🧠 Remplacement robuste via position des entités

Par défaut, les remplacements dans les fichiers texte se faisaient par correspondance directe de chaînes.  
Cela peut poser problème si le mot apparaît en plusieurs endroits ou est contenu dans d'autres mots.

Une approche plus robuste consiste à utiliser les **positions exactes** des entités (`start_char`, `end_char`)  
retournées par spaCy pour reconstruire le texte en injectant précisément les remplacements.

✅ Cela permet :
- D’éviter les collisions (ex : remplacer « Jean » dans « Jean-Michel »)
- De garantir que seule l’entité détectée est anonymisée
- Une future adaptation facile pour les formats comme `.txt` ou `.csv`

Cette méthode est désormais utilisée dans notre prototype de remplacement par position.


## 🚧 Roadmap

- [x] Support des fichiers `.docx` / `.xlsx`
- [x] Support des fichiers `.csv` / `.txt`
- [x] Log CSV des entités détectées
- [x] Sélection dynamique des types d'entités à anonymiser
- [ ] Remplacement plus robuste via indexation de positions
- [ ] Interface utilisateur (GUI)
- [ ] Traitement en batch

---

## 📦 Installation

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

---

## 🛡️ Licence

MIT - Simon Grossi
