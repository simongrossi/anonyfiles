# 🖼️ Anonyfiles GUI

**Anonyfiles GUI** est l’interface graphique moderne du projet [anonyfiles](https://github.com/simongrossi/anonyfiles).
Elle permet d’anonymiser facilement des fichiers textes grâce à une interface claire, rapide, et ergonomique, tout en utilisant la puissance du moteur CLI Python sous-jacent.

---

## 🚀 Fonctionnalités

* Drag & Drop de fichiers `.txt`, aperçu instantané du contenu.
* Zone de saisie de texte avec anonymisation à la volée.
* Sélection des types d’entités à anonymiser (personnes, lieux…).
* Affichage des résultats en temps réel.
* Copie en un clic du texte anonymisé (avec confirmation visuelle).
* Intégration native avec le moteur Python via Tauri.
* Thème sombre et design responsive (adapté aux petits écrans).
* **Totalement portable** : pas de chemin codé en dur, fonctionne sur n’importe quel PC.

---

## 🛠️ Installation & Prérequis

### Prérequis

* [Node.js](https://nodejs.org/) v18 ou supérieur
* [npm](https://www.npmjs.com/) ou [pnpm](https://pnpm.io/)
* [Rust](https://rustup.rs/) (pour Tauri)
* Python 3.9+ installé sur la machine
* Le dossier `anonyfiles-cli` doit être présent **à côté** du dossier `anonyfiles-gui`

### Installation

```sh
# Cloner le projet racine (si ce n’est pas déjà fait)
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles/anonyfiles-gui

# Installer les dépendances Node
npm install

# (facultatif) Installer Tauri s’il manque
npm install -g @tauri-apps/cli

# Démarrer le mode développement
npm run tauri dev
```

---

## 🖱️ Utilisation

* **Saisie manuelle ou glisser-déposer** d’un fichier texte.
* **Cochez** ou décochez les entités à anonymiser.
* Cliquez sur **Anonymiser**.
* Récupérez le résultat, copiez-le ou téléchargez-le.

---

## 📂 Structure du dossier

```
anonyfiles-gui/
│
├── src/
│   ├── lib/
│   │   └── DropZone.svelte      # Composant glisser-déposer
│   ├── App.svelte               # Composant racine
│   └── ...                      # Autres composants
├── src-tauri/                   # Backend Rust (pont vers Python CLI)
├── anonyfiles_outputs/          # Dossier de sortie (temp)
├── tailwind.config.cjs          # Config TailwindCSS
├── package.json                 # Dépendances Node
└── README.md                    # Ce fichier
```

---

## 🤖 Intégration avec la CLI

La GUI déclenche, en interne, l’exécution de la CLI Python `anonyfiles-cli/main.py` avec des chemins relatifs.
**Ne modifiez jamais la structure de dossiers** sans mettre à jour la logique des chemins dynamiques dans le code Rust.

---

## 🧑‍💻 Pour les développeurs

* Tout le style passe par **Tailwind CSS**.
* Architecture [Svelte](https://svelte.dev/) + [Tauri](https://tauri.app/).
* Les modifications front n’affectent pas la CLI Python (et vice-versa).
* Les fichiers temporaires sont placés dans `anonyfiles_outputs/` (jamais dans `cli`).

---

## 🐞 Dépannage

* **Erreur : main.py introuvable**
  → Vérifiez que le dossier `anonyfiles-cli` est bien dans le même dossier parent que `anonyfiles-gui`.

* **Erreur : Python non trouvé**
  → Ajoutez Python à votre PATH.

* **Autre bug ?**
  → Lancez la GUI depuis la racine du dossier et ouvrez une Issue sur GitHub avec vos logs et votre OS.

---

## 📝 Licence

Ce projet est open-source sous licence MIT.

---

## ✨ Auteur

Développé par [@simongrossi](https://github.com/simongrossi) et contributeurs.
Pour toute question : ouvrez une issue ou contactez-moi sur GitHub.
