# 🖼️ Anonyfiles GUI

**Anonyfiles GUI** est l’interface graphique multiplateforme d’Anonyfiles,  
développée en Svelte, Rust et Tauri pour une expérience utilisateur moderne et efficace.

---

## 🚀 Fonctionnalités

- Glisser-déposer de fichiers texte (.txt, .csv) ou sélection par dialogue  
- Zone de saisie manuelle pour anonymisation à la volée  
- Sélection intuitive des types d’entités à anonymiser (Personnes, Lieux, Organisations, Emails, Dates, etc.)  
- Affichage immédiat du texte anonymisé  
- Copie en un clic du résultat (avec confirmation visuelle)  
- Indicateurs de progression et gestion avancée des erreurs  
- Thème sombre / responsive pour une expérience fluide sur desktop et laptop  
- **Aucune dépendance à un serveur externe** : tout le traitement reste local  

---

## 🛠️ Prérequis & Installation

- [Node.js](https://nodejs.org/)  
- [Rust](https://www.rust-lang.org/tools/install)  
- [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites/)  
- [Python 3.9+](https://www.python.org/downloads/) avec le projet [anonyfiles_cli](https://github.com/simongrossi/anonyfiles) installé et accessible dans le `PATH`  

```sh
cd anonyfiles_gui
npm install
npm run tauri dev
```

---

## 💡 Utilisation

Lancez l’application :

```sh
npm run tauri dev
```

- Glissez-déposez un fichier texte (.txt, .csv) ou collez du texte brut dans la zone dédiée  
- Sélectionnez les entités à anonymiser selon vos besoins  
- Cliquez sur "Anonymiser"  
- Copiez ou enregistrez le texte anonymisé  

---

## 📸 Capture d’écran

![alt text](https://i.imgur.com/prsZuAy.jpeg)

---

## 🤖 Intégration avec le CLI

La GUI exploite le moteur Python (`anonyfiles_cli`) via une commande Rust/Tauri.  
Veillez à ce que `anonyfiles_cli` (et Python) soit installé et accessible dans votre environnement système (`PATH`).

---

## 🧩 Roadmap / Améliorations prévues

- ✅ Support natif drag & drop des fichiers Word (.docx), Excel (.xlsx), PDF et JSON  
- ✅ Paramétrage visuel avancé (choix du type de remplacement, simulation, exclusion...)  
- ✅ Prévisualisation enrichie et gestion multi-fichiers  
- ✅ Internationalisation (fr/en)  
- ✅ Export des résultats (mapping, journal d’entités)  
- ✅ Signatures logicielles et installeur .exe/macOS/Linux  
- ✅ Export intelligent selon le format d’entrée  
- ✅ Nom et extension du fichier exporté adaptés (.txt, .csv, .xlsx, etc.)  
- ✅ Sélection du format à l’export (TXT, CSV, XLSX…)  
- ✅ Aperçu avant/après (“split view”)  
- ✅ Comparaison directe original/anonymisé, bascule possible  
- ✅ Indicateur du volume traité (lignes, caractères, entités anonymisées)  
- ✅ Affichage des entités anonymisées (tableau récapitulatif, audit trail, export du mapping)  
- ✅ Barre de progression (progression réelle ou spinner)  
- ✅ Historique des traitements et profils d’anonymisation sauvegardables  
- ✅ Éditeur YAML intégré pour utilisateurs avancés  
- ✅ Notifications et raccourcis clavier (feedback utilisateur avancé)  
- ✅ Personnalisation de l’interface (mode sombre/clair, branding/logo)  
- ✅ Bandeau de confidentialité (“Aucune donnée n’est transmise en ligne”, suppression auto fichiers temp)  
- ✅ Améliorations UX diverses (drag & drop global, transitions de succès, temps de traitement)  

---

## 📜 Licence

MIT
