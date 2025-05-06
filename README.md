
# 🕵️ anonyfiles

**anonyfiles** est un outil open source d’anonymisation de documents, basé sur `spaCy`.  
Il se décline en deux interfaces complémentaires :

- 🖥️ **anonyfiles-gui** : une interface graphique moderne avec Tauri + Svelte.
- 💻 **anonyfiles-cli** : une ligne de commande Python robuste.

---

## ⚠️ Statut du projet

**anonyfiles est actuellement en phase de test.**  
Des bugs peuvent subsister et certaines fonctionnalités sont encore en cours de validation ou d'amélioration.  
Merci de faire preuve de vigilance et de ne pas l’utiliser sur des documents sensibles en production sans vérification.

---

## 🗂️ Détail de la structure du projet

```
anonyfiles/
├── anonyfiles-cli/      ← Interface en ligne de commande (CLI)
│   │   Ce dossier contient le code source de l'interface en ligne de commande, écrite en Python.
│   │   Il inclut les scripts pour l'anonymisation des différents types de fichiers (.docx, .xlsx, .csv, .txt) ainsi que les modules de traitement du texte et de remplacement des entités.
│   │
│   ├── anonymizer/    ← Modules d'anonymisation
│   │   │   Ce dossier contient les différents modules et classes nécessaires à l'anonymisation du texte.
│   │   │
│   │   │   ├── anonymizer_core.py  ← Logique principale de l'anonymisation
│   │   │   ├── csv_processor.py    ← Traitement des fichiers CSV
│   │   │   ├── excel_processor.py  ← Traitement des fichiers Excel
│   │   │   ├── replacer.py         ← Génération des remplacements
│   │   │   ├── spacy_engine.py     ← Moteur spaCy pour la détection des entités
│   │   │   ├── txt_processor.py      ← Traitement des fichiers TXT
│   │   │   └── word_processor.py   ← Traitement des fichiers Word
│   │   │
│   │   ├── input_files/   ← Fichiers d'entrée de test
│   │   ├── log/           ← Fichiers de log (si optionnel)
│   │   ├── main.py        ← Script principal de la CLI
│   │   └── requirements.txt ← Dépendances Python
│   │
├── anonyfiles-gui/      ← Interface graphique (GUI)
│   │   Ce dossier contient le code source de l'interface graphique, développée avec Tauri (Rust) et Svelte (JavaScript).
│   │   Il inclut les fichiers de l'interface utilisateur, la logique de l'application et la configuration de Tauri.
│   │
│   ├── public/       ← Assets statiques (HTML, etc.)
│   ├── src/          ← Code source Svelte
│   ├── src-tauri/    ← Code source et configuration Tauri (Rust)
│   │   │   ├── capabilities/  ← Permissions de l'application
│   │   │   ├── src/           ← Code Rust de Tauri
│   │   │   ├── tauri.conf.json ← Configuration de Tauri
│   │   │   └── vite.config.ts  ← Configuration de Vite
│   │   │
│   │   ├── index.html    ← Page HTML principale
│   │   ├── package.json  ← Dépendances et scripts Node.js
│   │   ├── package-lock.json
│   │   ├── README.md
│   │   └── tsconfig.json  ← Configuration TypeScript
│   │
├── README.md         ← Documentation principale
└── LICENSE           ← Licence du projet

---

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

## 🚀 Utilisation CLI (anonyfiles-cli)

### 📦 Installation

```bash
cd anonyfiles-cli
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

### ▶️ Exemples

Anonymisation d’un document :
```bash
python main.py input_files/mon_fichier.docx
```

Avec export des entités détectées :
```bash
python main.py mon_fichier.docx --log-entities log/entites.csv
```

Avec filtrage sur types d’entités :
```bash
python main.py mon_fichier.docx --entities PER ORG
```

---

## 📝 Export CSV des entités détectées

Le fichier CSV généré avec `--log-entities` contiendra :
- **Entite** : le texte trouvé
- **Label** : son type (`PER`, `LOC`, `ORG`, etc.)

---

## 🔧 Types d'entités disponibles

Dépend du modèle spaCy `fr_core_news_md`. Exemples courants :
- `PER` : Personnes
- `LOC` : Lieux
- `ORG` : Organisations
- `DATE` : Dates
- `MISC` : Divers

---

## 🧠 Remplacement via positions précises (prototype)

Pour éviter les collisions ou erreurs, l’algorithme utilise désormais les **positions (`start_char`, `end_char`)** des entités dans le texte.  
Cela garantit une anonymisation plus fiable, notamment dans les `.txt` et `.csv`.

---

## 🖥️ Interface graphique (`anonyfiles-gui`) – ❌ NON FONCTIONNELLE

⚠️ L'interface graphique est actuellement **non opérationnelle**. Plusieurs problèmes bloquants empêchent son lancement :

- 🚫 **Échec de la construction de l'interface** : le dossier `dist` requis par Tauri n’est pas généré.
- ❌ **Erreurs de chargement des assets** (JS/CSS) : Tauri affiche une page blanche ou des erreurs en console.
- 🔌 **Connexion impossible au serveur de développement Vite**.

### 🔧 Prérequis techniques (si contribution souhaitée)

- Node.js (≥18)
- Rust (via `rustup`)
- Tauri CLI :

```bash
npm install -g @tauri-apps/cli
```

### 🚀 Commandes de développement (non fonctionnelles à ce jour)

```bash
cd anonyfiles-gui
npm install
npm run tauri dev
```

### 🤝 Appel à contribution

> Si vous maîtrisez Svelte, Vite ou Tauri et souhaitez aider à stabiliser l'interface graphique, toute contribution est la bienvenue ! 🙏

---

## 🚧 Roadmap

- [x] Support `.docx`, `.xlsx`, `.csv`, `.txt`
- [x] Sélection dynamique des entités
- [x] Export CSV des entités détectées
- [o] Interface GUI avec Tauri (v2)
- [ ] Drag & Drop dans l’interface
- [ ] Traitement en batch
- [ ] Packaging multiplateforme (Windows/macOS/Linux)

---

## 🛡️ Licence

MIT - Simon Grossi
