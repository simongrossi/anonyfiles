# 🖼️ Anonyfiles GUI

**Anonyfiles GUI** est l’interface graphique multiplateforme d’Anonyfiles,
développée en Svelte, Rust et Tauri pour une expérience utilisateur moderne et efficace.

---

## 🚀 Fonctionnalités

* Glisser-déposer de fichiers texte (.txt, .csv) ou sélection par dialogue
* Zone de saisie manuelle pour anonymisation à la volée
* Sélection intuitive des types d’entités à anonymiser (Personnes, Lieux, Organisations, Emails, Dates, etc.)
* Affichage immédiat du texte anonymisé
* Copie en un clic du résultat (avec confirmation visuelle)
* Indicateurs de progression et gestion avancée des erreurs
* Thème sombre / responsive pour une expérience fluide sur desktop et laptop
* **Aucune dépendance à un serveur externe** : tout le traitement reste local

---

## 🛠️ Prérequis & Installation

* [Node.js](https://nodejs.org/)
* [Rust](https://www.rust-lang.org/tools/install)
* [Tauri CLI](https://tauri.app/v1/guides/getting-started/prerequisites/)
* [Python 3.9+](https://www.python.org/downloads/) avec le projet [anonyfiles-cli](https://github.com/simongrossi/anonyfiles) installé et accessible dans le PATH

```sh
cd anonyfiles-gui
npm install
npm run tauri dev
```

---

## 💡 Utilisation

1. Lancez l’application :

   ```sh
   npm run tauri dev
   ```
2. Glissez-déposez un fichier texte (.txt, .csv) **ou** collez du texte brut dans la zone dédiée
3. Sélectionnez les entités à anonymiser selon vos besoins
4. Cliquez sur "Anonymiser"
5. Copiez ou enregistrez le texte anonymisé

---

## 📸 Capture d’écran

![alt text](https://i.imgur.com/prsZuAy.jpeg)

---

## 🤖 Intégration avec le CLI

La GUI exploite le moteur Python (`anonyfiles-cli`) via une commande Rust/Tauri.
Veillez à ce que `anonyfiles-cli` (et Python) soit installé et accessible dans votre environnement système (PATH).

---

## 🧩 Roadmap / Améliorations prévues

* Support natif drag & drop des fichiers Word (.docx), Excel (.xlsx), PDF et JSON  
* Paramétrage visuel avancé (choix du type de remplacement, simulation, exclusion...)  
* Prévisualisation enrichie et gestion multi-fichiers  
* Internationalisation (fr/en)  
* Export des résultats (mapping, journal d’entités)  
* Signatures logicielles et installeur .exe/macOS/Linux  
* **Export intelligent selon le format d’entrée**  
  - Nom et extension du fichier exporté adaptés (.txt, .csv, .xlsx, etc.)  
  - Sélection du format à l’export (TXT, CSV, XLSX…)  
* **Aperçu avant/après (“split view”)**  
  - Comparaison directe original/anonymisé, bascule possible  
* **Indicateur du volume traité**  
  - Nombre de lignes, caractères, entités anonymisées  
* **Affichage des entités anonymisées**  
  - Tableau récapitulatif, audit trail, export du mapping  
* **Barre de progression**  
  - Affichage progression réelle ou spinner lors de l’anonymisation  
* **Historique des traitements** et profils d’anonymisation sauvegardables  
* **Éditeur YAML intégré** pour utilisateurs avancés  
* **Notifications et raccourcis clavier** (feedback utilisateur avancé)  
* **Personnalisation de l’interface**  
  - Mode sombre/clair, branding/logo  
* **Bandeau de confidentialité**  
  - “Aucune donnée n’est transmise en ligne”, suppression auto fichiers temp  
* **Améliorations UX diverses**  
  - Drag & drop global (toute la fenêtre), transitions de succès, affichage du temps de traitement  


---

## 📜 Licence

MIT
