# 🛡️ anonyfiles

**Anonyfiles** est une application Python open source permettant d'**anonymiser automatiquement des fichiers Word (.docx) et Excel (.xlsx)** en local.  
Elle détecte les données personnelles (noms, prénoms, dates, adresses, organisations, etc.) à l'aide de l'IA open source **spaCy**, puis les remplace ou les masque selon vos besoins.

---

## 🎯 Objectif

Fournir un outil **multiplateforme, local et RGPD-compliant**, pour anonymiser efficacement les documents contenant des données sensibles.

---

## ⚙️ Fonctionnalités

- ✅ Détection automatique des entités personnelles (noms, lieux, dates…)
- 🧠 Utilisation de **spaCy** en local (aucune donnée envoyée)
- 📄 Support des formats **Word (.docx)** et **Excel (.xlsx)**
- 🔁 Remplacement configurable : données fictives (`Faker`) ou texte `[REDACTED]`
- 📤 Export CSV facultatif des entités détectées (`--log-entities`)
- 💾 Génération d’un fichier anonymisé dans `output_files/`

---

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/anonyfiles.git
cd anonyfiles
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
venv\Scripts\activate    # Sous Windows
source venv/bin/activate   # Sous macOS/Linux
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

---

## 🚀 Utilisation

### Anonymiser un fichier Word :

```bash
python main.py test.docx
```

### Anonymiser avec journalisation CSV des entités :

```bash
python main.py test.docx --log-entities entites_test.csv
```

Le log sera généré dans `log/entites_test.csv` (sauf si un chemin complet est fourni).

---

## 📁 Structure du projet

```
anonyfiles/
├── anonymizer/
│   ├── spacy_engine.py
│   ├── word_processor.py
│   ├── excel_processor.py
│   └── replacer.py
├── input_files/
├── output_files/
├── log/
├── main.py
├── requirements.txt
└── README.md
```

---

## 🔐 Pourquoi en local ?

Contrairement à des solutions cloud :
- ✅ Aucune connexion internet requise
- ✅ Conformité RGPD renforcée
- ✅ Meilleur contrôle des documents sensibles

---

## 📋 Roadmap

- [x] Support Word et Excel
- [x] Export CSV des entités détectées
- [ ] Interface graphique simple (Tauri, PyQt, Tkinter)
- [ ] Support PDF avec OCR (Tesseract)
- [ ] Paramétrage fin des types d’entités à anonymiser
- [ ] Exécution par dossier complet
- [ ] Packaging `.exe` (PyInstaller)

---

## 📄 Licence

Ce projet est sous licence **MIT**.

---

## 🤝 Contribuer

Les contributions sont bienvenues !
- Bugs
- Idées de fonctionnalités
- Revue de code
- Traductions

N'hésitez pas à forker le projet et soumettre une PR !
