# 🖼️ Anonyfiles GUI

**Anonyfiles GUI** est l’interface graphique multiplateforme d’Anonyfiles,  
développée en Svelte, Rust et Tauri pour une expérience utilisateur moderne et efficace.

---

## 🚀 Fonctionnalités

- Glisser-déposer de fichiers texte (.txt, .csv) ou sélection par dialogue  
- Zone de saisie manuelle pour anonymisation à la volée  
- Sélection intuitive des types d’entités à anonymiser (Personnes, Lieux, Organisations, Emails, Dates, etc.)  
- Profils d’anonymisation prêts à l’emploi : strict RGPD, léger, documents RH, contrats, logs techniques
- Prévisualisation des entités détectées avant anonymisation finale, avec exclusion ou correction du type
- Affichage immédiat du texte anonymisé  
- Copie en un clic du résultat (avec confirmation visuelle)  
- Indicateurs de progression et gestion avancée des erreurs  
- Thème sombre / responsive pour une expérience fluide sur desktop et laptop  
- **Aucune dépendance à un serveur externe** : tout le traitement reste local  

---

## 🛠️ Prérequis & Installation

- [Node.js 22+](https://nodejs.org/)
- [Rust stable](https://www.rust-lang.org/tools/install)
- Python 3.11+ pour builder le sidecar Python/FastAPI
- Dépendances Python installées depuis la racine via `pyproject.toml`

```sh
cd ..
python -m pip install -e .
python -m spacy download fr_core_news_md
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

## 🤖 Intégration avec l'API locale

La GUI parle à l'API FastAPI (`anonyfiles_api`). En desktop, Tauri lance le
sidecar Python embarqué ; en développement, vous pouvez aussi lancer Uvicorn à
part avec `python -m anonyfiles_api --host 127.0.0.1 --port 8000`.

Si cette API externe active `ANONYFILES_API_KEY`, définissez
`VITE_ANONYFILES_API_KEY` côté GUI pour ajouter automatiquement le header
`X-API-Key`. Cette valeur est visible dans un bundle web public ; réservez-la
aux déploiements privés ou au desktop.

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
- ✅ Profils d’anonymisation prêts à l’emploi avec réglages manuels conservés
- ✅ Prévisualisation des entités détectées avant traitement final
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
