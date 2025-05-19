# 🖼️ Anonyfiles GUI

**Anonyfiles GUI** est l’interface graphique multiplateforme d’Anonyfiles,  
développée en Svelte, Rust et Tauri pour une expérience utilisateur moderne et efficace.

---

## 🚀 Fonctionnalités

- Glisser-déposer de fichiers texte ou sélection par dialogue
- Zone de saisie manuelle pour anonymisation à la volée
- Sélection intuitive des types d’entités à anonymiser (Personnes, Lieux, Orgs, Emails, Dates…)
- Affichage immédiat du texte anonymisé
- Copie en un clic du résultat (avec confirmation visuelle)
- Indicateurs de progression, gestion des erreurs
- Thème sombre / responsive (expérience fluide desktop)
- **Aucune dépendance à un serveur externe** (tout local)

---

## 🛠️ Prérequis & Installation

- [Node.js](https://nodejs.org/)
- [Rust](https://www.rust-lang.org/tools/install)
- [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites/)

```sh
cd anonyfiles-gui
npm install
npm run tauri dev
💡 Utilisation
Lancer l’application (npm run tauri dev)

Glisser-déposer un fichier texte ou coller du texte brut dans la zone prévue

Cocher/décocher les entités à anonymiser selon besoin

Cliquer sur "Anonymiser"

Copier ou enregistrer le texte anonymisé

📸 Capture d’écran
(Insérer ici une capture de l’interface, optionnel)

🤖 Intégration CLI
La GUI utilise le moteur CLI Python sous le capot (via Tauri/Rust)
Assurez-vous que anonyfiles-cli et Python sont accessibles depuis votre environnement.

🧩 Roadmap / Améliorations prévues
Support natif des fichiers Word, Excel, PDF, JSON en drag & drop

Paramétrage visuel avancé (options de remplacement, simulation…)

Internationalisation

📜 Licence
MIT