# 🛡️ anonyfiles

**Anonyfiles** est une application Python open source permettant d'**anonymiser automatiquement des fichiers Word (.docx) et Excel (.xlsx)** en local. Elle détecte les données personnelles (noms, prénoms, dates, adresses, etc.) à l'aide de l'IA open source **spaCy**, puis les remplace ou les masque selon vos besoins.

---

## 🎯 Objectif

Fournir un outil **multiplateforme, 100 % local et RGPD-compliant**, pour anonymiser efficacement les documents contenant des données sensibles.

---

## ⚙️ Fonctionnalités

- ✅ Détection automatique des entités personnelles (noms, lieux, dates…)
- 🧠 Utilisation de **spaCy** en local (pas d'envoi de données)
- 📄 Support des formats **Word (.docx)** et **Excel (.xlsx)**
- 🔁 Remplacement configurable (balises ou données fictives via `Faker`)
- 💾 Génération d’un nouveau fichier anonymisé

---

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/anonyfiles.git
cd anonyfiles
```

### 2. Créer un environnement virtuel (optionnel mais recommandé)

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Télécharger le modèle spaCy français (si ce n’est pas déjà fait)

```bash
python -m spacy download fr_core_news_md
```

---

## 🚀 Utilisation rapide

Placez un fichier `.docx` ou `.xlsx` dans le dossier `input_files/`.

Exemple avec un fichier Word :

```bash
python main.py
```

L’application :
1. Lit le document
2. Identifie les données personnelles
3. Génère un fichier anonymisé dans `output_files/mon_fichier_anonymise.docx`

---

## 📁 Structure du projet

```
anonyfiles/
├── main.py
├── requirements.txt
├── anonymizer/
│   ├── spacy_engine.py
│   ├── word_processor.py
│   ├── excel_processor.py
│   └── replacer.py
├── input_files/
├── output_files/
└── README.md
```

---

## 🔐 Pourquoi en local ?

Contrairement à d'autres solutions cloud, **anonyfiles fonctionne entièrement en local** :
- ✅ Aucune dépendance à internet
- ✅ Conformité RGPD renforcée
- ✅ Meilleur contrôle des données sensibles

---

## 📋 Roadmap (à venir)

- [ ] Interface graphique simple (Tauri, PyQt…)
- [ ] Support de fichiers PDF (via OCR)
- [ ] Mode ligne de commande avec options
- [ ] Export des entités détectées (fichier CSV/log)

---

## 📄 Licence

Ce projet est sous licence **MIT**. Vous êtes libre de l'utiliser, le modifier et le redistribuer.

---

## 🤝 Contribuer

Les contributions sont les bienvenues !  
N'hésitez pas à proposer des idées, corriger des bugs ou soumettre des PR.
