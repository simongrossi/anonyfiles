# 🕵️‍♂️ Anonyfiles

**Anonyfiles** est une solution open source complète pour l’anonymisation automatisée de documents texte, tableurs et bureautiques, basée sur le NLP (spaCy) et des stratégies avancées de remplacement (Faker, codes, placeholders, etc.).

* **CLI (`anonyfiles-cli`)** : traitement en ligne de commande, configurable, robuste et multi-format.
* **GUI (`anonyfiles-gui`)** : interface graphique moderne (Tauri + Svelte + Rust) pour une anonymisation intuitive, rapide et multiplateforme.
* **API (`anonyfiles_api`)** : API REST FastAPI pour intégration dans des workflows ou systèmes tiers.

---

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
├── anonyfiles-cli/            # Outil CLI (Python)
│   └── README.md              # Documentation CLI détaillée
├── anonyfiles-gui/            # Interface graphique (Tauri / Svelte)
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

➡️ Voir [`anonyfiles-cli/README.md`](anonyfiles-cli/README.md)

### Installation GUI

➡️ Voir [`anonyfiles-gui/README.md`](anonyfiles-gui/README.md)

- Interface graphique moderne (Svelte + Rust via Tauri)
- Drag & drop, sélection intuitive des entités à anonymiser
- Mode sombre, responsive, traitement local sécurisé
- Copie et prévisualisation des résultats

![Aperçu de l'interface graphique](https://i.imgur.com/OEq7Q9W.jpeg)

### Lancement de l’API

➡️ Voir [`anonyfiles_api/README.md`](anonyfiles_api/README.md)

---

## 📖 Documentation détaillée

* **CLI :** Voir [`anonyfiles-cli/README.md`](anonyfiles-cli/README.md)
* **GUI :** Voir [`anonyfiles-gui/README.md`](anonyfiles-gui/README.md)
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
