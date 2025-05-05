# 🕵️ anonyfiles

**anonyfiles** est un outil open source d’anonymisation de documents, basé sur `spaCy`. Il prend en charge les formats Word, Excel, CSV et TXT.

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
