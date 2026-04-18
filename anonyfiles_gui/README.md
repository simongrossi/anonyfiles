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

- [Node.js 20+](https://nodejs.org/) & npm
- [Rust stable](https://www.rust-lang.org/tools/install) & Cargo
- Python 3.11+ (pour builder le sidecar qui embarque l'API)

Deux scénarios d'installation, à choisir selon ce que tu veux faire :

### Lancement en dev (Tauri dev)

Le build du sidecar est un préalable une fois, puis `npm run tauri dev` utilise le binaire produit :

```sh
# depuis la racine du repo
make sidecar                  # produit anonyfiles-api-<triple> dans src-tauri/binaries/
cd anonyfiles_gui
npm install
npm run tauri dev             # ouvre la fenêtre, spawne le sidecar au démarrage
```

Alternative : lancer un `uvicorn` externe sur le port 8000 et pointer la GUI vers lui via `VITE_ANONYFILES_API_URL=http://127.0.0.1:8000`. Plus rapide pour itérer sur l'API sans rebuilder le sidecar à chaque fois.

### Application autonome distribuable

Depuis la racine du repo :

```sh
make desktop
```

Produit un `.app` / `.dmg` / `.msi` / `.exe` / `.AppImage` / `.deb` dans `src-tauri/target/release/bundle/` selon la plateforme. Voir [`guide_installation_anonyfiles.md`](../guide_installation_anonyfiles.md#-application-desktop-autonome) pour les détails.

---

## 💡 Utilisation

- Glissez-déposez un fichier texte (.txt, .csv) ou collez du texte brut dans la zone dédiée
- Sélectionnez les entités à anonymiser selon vos besoins
- Cliquez sur "Anonymiser"
- Copiez ou enregistrez le texte anonymisé

Au tout premier lancement, un overlay « Démarrage du moteur NER… » reste affiché ~15-25 s pendant le chargement du modèle spaCy par le sidecar.

---

## 📸 Capture d’écran

![alt text](https://i.imgur.com/prsZuAy.jpeg)

---

## 🤖 Architecture

La GUI (Svelte + TypeScript) ne contient aucun code NLP. Toute l'anonymisation passe par HTTP vers l'API FastAPI (`anonyfiles_api`), exactement comme la version web.

En mode **desktop**, Tauri (`src-tauri/src/main.rs`) spawne le sidecar `anonyfiles-api-<triple>` (binaire PyInstaller contenant FastAPI + uvicorn + spaCy + modèle FR) sur un port libre choisi aléatoirement, puis expose ce port au frontend via la commande Tauri `get_api_port`. Le sidecar est tué automatiquement à la fermeture de la fenêtre.

En mode **web**, la GUI (servie par nginx dans le compose Docker) pointe vers l'API distante définie par `VITE_ANONYFILES_API_URL`.

Voir [`src-tauri/README.md`](src-tauri/README.md) pour le détail Rust et [`anonyfiles_architecture.md`](../anonyfiles_architecture.md) pour la vue d'ensemble.

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
