# 🕵️‍♂️ Anonyfiles

**Anonyfiles** est une solution open source complète pour l’anonymisation automatisée de documents texte, tableurs et bureautiques, basée sur le NLP (spaCy) et des stratégies avancées de remplacement (Faker, codes, placeholders, etc.).

* **CLI (anonyfiles-cli)** : traitement en ligne de commande, configurable, robuste et multi-format.
* **GUI (anonyfiles-gui)** : interface graphique moderne (Tauri + Svelte + Rust) pour une anonymisation intuitive, rapide et multiplateforme.

---

## 🚀 Fonctionnalités principales

* Anonymisation de fichiers : `.txt`, `.csv`, `.docx`, `.xlsx`, `.pdf`, `.json`
* Détection automatique de noms, lieux, organisations, dates, emails, etc.
* Stratégies configurables : remplacement factice, `[REDACTED]`, codes séquentiels, etc.
* Mapping complet pour désanonymisation ou audit
* Export CSV des entités détectées
* Sélection fine des entités à anonymiser (interface graphique ou CLI)
* Prise en charge du français (et autres langues via spaCy)
* **Portable** : aucun chemin codé en dur, multiplateforme (Windows, macOS, Linux)

---

## 🗂️ Structure du projet

```plaintext
anonyfiles/
│
├── README.md                # Présent fichier
├── anonyfiles-cli/          # Outil en ligne de commande (Python)
│   └── README.md            # Doc CLI détaillée
├── anonyfiles-gui/          # Interface graphique Tauri (Svelte/Rust)
│   └── README.md            # Doc GUI détaillée
└── ...                      # Données, configs, tests, docs
```

---

## 📦 Installation rapide

### Pré-requis

* Python 3.8+ (pour la CLI)
* Node.js 18+, npm/yarn (pour la GUI)
* Rust & Cargo (pour la GUI)

### Clonage du projet

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
```

### Installation CLI

Voir [`anonyfiles-cli/README.md`](anonyfiles-cli/README.md)

### Installation GUI

Voir [`anonyfiles-gui/README.md`](anonyfiles-gui/README.md)

---

## 📖 Documentation détaillée

* **CLI :** Voir [`anonyfiles-cli/README.md`](anonyfiles-cli/README.md) pour l’utilisation, la configuration, et les formats supportés.
* **GUI :** Voir [`anonyfiles-gui/README.md`](anonyfiles-gui/README.md) pour l’installation, la prise en main, et les options avancées.

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

*Pour toute question, consultez la documentation CLI/GUI ou ouvrez une issue sur GitHub.*
