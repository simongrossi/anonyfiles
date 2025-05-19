# 🕵️‍♂️ anonyfiles-gui

**anonyfiles-gui** est l’interface graphique moderne et officielle du projet [anonyfiles](https://github.com/simongrossi/anonyfiles).
Elle vous permet d’anonymiser facilement vos fichiers textes via une interface épurée, rapide et intuitive, tout en s’appuyant sur la puissance du moteur CLI Python du projet principal.

---

## 🚀 Fonctionnalités

- **Glisser-déposer** (drag & drop) de fichiers `.txt` et aperçu du contenu.
- **Zone de saisie** pour l’anonymisation de texte à la volée.
- **Sélection des entités à anonymiser** (personnes, lieux...).
- **Affichage instantané** du texte anonymisé, avec copie en un clic (toast “Copié !”).
- **Thème sombre** responsive, design épuré et accessible.
- **Feedbacks visuels** (loading, drag, toast, erreurs...).
- **Intégration native** avec le moteur Python via Tauri (Rust bridge).
- **Aucun chemin codé en dur** : portable sur n’importe quel poste.

---

## 🛠️ Installation & Prérequis

### Prérequis

- [Node.js](https://nodejs.org/) v18 ou supérieur
- [npm](https://www.npmjs.com/) ou [pnpm](https://pnpm.io/)
- [Rust](https://rustup.rs/) (pour Tauri)
- Python 3.9+ (avec les dépendances du projet CLI)
- Le dossier `anonyfiles-cli` doit être **à côté** du dossier `anonyfiles-gui`

### Installation

```sh
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles/anonyfiles-gui
npm install
# (facultatif) Installer Tauri si besoin
npm install -g @tauri-apps/cli
# Lancer en mode développement
npm run tauri dev
🖱️ Utilisation
Glissez-déposez un fichier texte ou saisissez/collez le texte à anonymiser.

Cochez ou décochez les entités à anonymiser.

Cliquez sur Anonymiser.

Copiez le résultat en un clic (toast visuel “Copié !”).

Visualisez, recommencez, ou passez à un autre fichier.

📂 Structure du projet
graphql
Copier
Modifier
anonyfiles/
├── anonyfiles-cli/        # Projet Python CLI (moteur)
└── anonyfiles-gui/        # GUI Svelte + Tailwind + Tauri
    ├── src/
    │   ├── App.svelte
    │   └── lib/
    │       ├── DropZone.svelte
    │       └── TextAnonymizer.svelte
    ├── src-tauri/         # Backend Rust (pont avec Python CLI)
    ├── anonyfiles_outputs/ # Temp files (jamais dans cli)
    ├── tailwind.config.cjs
    ├── package.json
    └── README.md          # Ce fichier
🤖 Intégration CLI
La GUI appelle en interne anonyfiles-cli/main.py avec des chemins dynamiques.
⚠️ Ne modifiez pas la structure des dossiers sans adapter les chemins dans le code Rust (src-tauri/main.rs).

🧑‍💻 Pour les devs
Le style est 100% Tailwind CSS.

Frontend Svelte (composants séparés : DropZone, TextAnonymizer, etc.)

Backend Rust (Tauri) : simple passerelle pour le CLI Python.

Tous les fichiers temporaires restent dans anonyfiles_outputs/ (jamais dans cli).

🐞 Dépannage
Erreur : main.py introuvable
→ Vérifiez que anonyfiles-cli est bien à côté de anonyfiles-gui.

Erreur : Python non trouvé
→ Ajoutez Python à votre PATH.

Bug ou question ?
→ Lancez la GUI depuis le dossier adéquat. Si besoin, ouvrez une Issue avec vos logs et OS.

📝 Licence
Ce projet est open-source sous licence MIT.

✨ Auteur
Développé par @simongrossi.
Pour toute question : ouvrez une issue GitHub ou contactez-moi directement.

