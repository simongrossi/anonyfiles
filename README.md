# 🕵️‍♂️ Anonyfiles

**Anonyfiles** est une solution open source complète pour l’anonymisation automatisée de documents texte, tableurs et fichiers bureautiques.  
Elle s’appuie sur des technologies de traitement du langage naturel (spaCy) et des stratégies avancées de remplacement (Faker, codes, placeholders, etc.).

## 🎯 Pourquoi ce projet ?

À force d’utiliser l’intelligence artificielle dans des cas variés, un besoin simple mais essentiel s’est imposé :  
👉 **pouvoir anonymiser rapidement des données textuelles avant de les soumettre à un traitement externe** (IA, workflow, audit, etc.).

Mais l’objectif ne s’arrêtait pas là :  
🔁 **Pouvoir désanonymiser un fichier traité** grâce à un mapping généré pendant l’anonymisation faisait aussi partie des ambitions du projet.  

Et comme je suis curieux et passionné, je me suis dit : autant en profiter pour aller plus loin  
🧠 **en créant une solution complète, modulaire et réutilisable**, avec API, CLI et interface graphique moderne.

---

## 🧩 Trois modules complémentaires

* **CLI (`anonyfiles_cli`)** : traitement en ligne de commande, configurable, robuste et multi-format.  
* **GUI (`anonyfiles_gui`)** : interface graphique moderne (Tauri + Svelte + Rust) pour une anonymisation intuitive, rapide et multiplateforme.  
* **API (`anonyfiles_api`)** : API REST (FastAPI) pour intégration dans des workflows automatisés ou systèmes tiers.


## 🚀 Fonctionnalités principales

* Anonymisation de fichiers : `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
* Détection automatique de noms, lieux, organisations, dates, emails, etc.
* Stratégies configurables : remplacement factice, `[REDACTED]`, codes séquentiels, etc.
* Mapping complet pour désanonymisation ou audit
* Export CSV des entités détectées
* Sélection fine des entités à anonymiser (interface graphique ou CLI)
* Prise en charge du français (et autres langues via spaCy)
* **Asynchrone via l’API REST** (suivi via `job_id`)
* **Portable** : aucun chemin codé en dur, multiplateforme (Windows, macOS, Linux)

---

## 🗂️ Structure du projet

```plaintext
anonyfiles/
│
├── README.md                  # Présent fichier
├── anonyfiles_cli/            # Outil CLI (Python)
│   └── README.md              # Documentation CLI détaillée
├── anonyfiles_gui/            # Interface graphique (Tauri / Svelte)
│   └── README.md              # Documentation GUI détaillée
├── anonyfiles_api/            # API FastAPI pour appel distant
│   └── README.md              # Documentation API détaillée
└── ...
```

---

## 📦 Installation rapide

### Pré-requis

* Python 3.11 (recommandé, testé en production)
* Node.js 18+, npm/yarn (pour la GUI)
* Rust & Cargo (pour la GUI)
* Modèle spaCy `fr_core_news_md`

### Clonage du projet

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
```

### Installation CLI

➡️ Voir [`anonyfiles_cli/README.md`](anonyfiles_cli/README.md)

![Aperçu de la CLI](https://i.imgur.com/GJksQfm.jpeg)


### Installation GUI

➡️ Voir [`anonyfiles_gui/README.md`](anonyfiles_gui/README.md)

- Interface graphique moderne (Svelte + Rust via Tauri)
- Drag & drop, sélection intuitive des entités à anonymiser
- Mode sombre, responsive, traitement local sécurisé
- Copie et prévisualisation des résultats

![Aperçu de l'interface graphique](https://i.imgur.com/LN3ib6y.jpeg)

### Lancement de l’API

➡️ Voir [`anonyfiles_api/README.md`](anonyfiles_api/README.md)

---

## ⚙️ Setup automatique des environnements

Afin d’isoler proprement les dépendances entre la CLI, l’API et la GUI, le projet utilise **trois environnements virtuels distincts** :

- `env-cli` → pour `anonyfiles_cli` (spaCy, typer…)
- `env-api` → pour `anonyfiles_api` (FastAPI, pydantic…)
- `env-gui` → pour les éventuelles dépendances Python liées à la GUI

Des scripts de configuration automatique sont disponibles à la racine du projet pour **Linux/macOS** et **Windows** :

### ▶️ Linux / macOS
### 🪟 Windows (PowerShell ou CMD)

#### PowerShell (recommandé)

```powershell
.nonyfiles.ps1 -action setup     # Crée les environnements
.nonyfiles.ps1 -action api       # Lance l’API FastAPI
.nonyfiles.ps1 -action cli       # Lance le moteur CLI
.nonyfiles.ps1 -action gui       # Lance la GUI (Tauri)
.nonyfiles.ps1 -action clean     # Supprime les environnements
```

#### CMD (invite de commande Windows classique)

```cmd
anonyfiles.bat setup    :: Crée les environnements
anonyfiles.bat api      :: Lance l’API
anonyfiles.bat cli      :: Lance le moteur CLI
anonyfiles.bat gui      :: Lance la GUI (Tauri)
anonyfiles.bat clean    :: Supprime les environnements
```

> 📁 Les scripts `anonyfiles.ps1` et `anonyfiles.bat` sont disponibles à la racine du projet.


```bash
chmod +x setup_envs.sh
./setup_envs.sh
```

### 🪟 Windows (PowerShell)

```powershell
.\setup_envs.ps1
```

Ces scripts effectuent les actions suivantes :

1. Créent trois environnements virtuels (`env-cli`, `env-api`, `env-gui`)
2. Installent automatiquement les dépendances listées dans :
   - `cli/requirements.txt`
   - `anonyfiles_api/requirements.txt`
   - `GUI/requirements.txt` *(optionnel)*

---

## 📖 Documentation détaillée

* **CLI :** Voir [`anonyfiles_cli/README.md`](anonyfiles_cli/README.md)
* **GUI :** Voir [`anonyfiles_gui/README.md`](anonyfiles_gui/README.md)
* **API :** Voir [`anonyfiles_api/README.md`](anonyfiles_api/README.md)

---

## 🛣️ Roadmap

| Priorité | Thème                                                | État           | Commentaire / Lien tâche                          |
|----------|------------------------------------------------------|----------------|---------------------------------------------------|
| 1        | Robustesse multi-format (TXT, CSV, DOCX, XLSX)       | ✅ Fait        | Moteur factorisé, détection commune               |
| 2        | Remplacement positionnel fiable                      | ⚠️ Test/Debug  | En cours de vérification                          |
| 3        | Détection universelle des dates et emails            | ✅ Fait        | Regex avancée + spaCy                             |
| 4        | Performance / gestion mémoire                        | 🔜 À venir     | Streaming, lazy processing                        |
| 5        | Règles de remplacement par type (YAML)               | ⚠️ Test/Debug  | Règles personnalisées en test                     |
| 6        | Mapping codes <-> originaux                          | ⚠️ Test/Debug  | Mapping inverse, audit, désanonymisation          |
| 7        | Filtre exclusion (YAML / CLI)                        | ✅ Fait        | Configurable, évite faux positifs                 |
| 8        | Support PDF / JSON                                   | 🔜 À venir     | PDF natif, JSON complet                           |
| 9        | Désanonymisation CLI (mapping inverse)               | ⚠️ Test/Debug  | Tests en cours                                    |
| 10       | GUI avancée (drag & drop, prévisualisation)          | 🚧 En cours    | Tauri/Svelte, UX moderne                          |
| 11       | Copie, export, gestion multi-fichier dans la GUI     | 🚧 En cours    | Copier/coller, sélection, batch                   |
| 12       | Support anglais, espagnol, allemand                  | 🔜 À venir     | Modèles spaCy additionnels                        |
| 13       | API asynchrone avec suivi de jobs (`job_id`)         | ✅ Fait        | CORS, UUID, audit log complet                     |

---

## 🤝 Contribuer

* Toute contribution est la bienvenue : bugfix, traduction, documentation, suggestion !
* Merci de créer une issue ou une PR avec un descriptif clair et un code lisible.

---

## 📄 Licence

Projet distribué sous licence MIT. Voir [LICENSE](LICENSE).

---

## 👨‍💻 Auteur & Liens

* Projet développé par [Simon Grossi](https://github.com/simongrossi)
* Repo GitHub principal : [https://github.com/simongrossi/anonyfiles](https://github.com/simongrossi/anonyfiles)

---

*Pour toute question, consultez la documentation CLI/GUI/API ou ouvrez une issue sur GitHub.*
