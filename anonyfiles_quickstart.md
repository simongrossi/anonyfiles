# ⚡ Démarrage Rapide

Vous êtes pressé ? Voici comment lancer **Anonyfiles** et anonymiser votre premier document en moins de 5 minutes, que vous soyez développeur ou utilisateur.

---

## 1️⃣ Via la Ligne de Commande (CLI)

Méthode la plus directe pour traiter des fichiers en local.

### Prérequis

Avoir installé le projet → voir `[[Installation]]`.

### Première anonymisation

```bash
anonyfiles-cli anonymize mon_cv.docx
```

Le fichier anonymisé sera créé dans un dossier :
```
anonyfiles_outputs/runs/...
```

### Mode interactif (recommandé)

Permet de choisir ce qu'il faut masquer (Noms, Emails, Lieux...).

```bash
anonyfiles-cli anonymize rapport.txt --interactive
```

---

## 2️⃣ Via Docker (API)

Idéal pour tester sans installer Python.

### Lancement

```bash
docker build -t anonyfiles . && docker run -p 8000:8000 anonyfiles
```

Une fois le serveur lancé :

1. Aller sur <http://localhost:8000/docs>
2. Cliquer sur `POST /anonymize`
3. Cliquer `Try it out`
4. Uploader un fichier
5. `Execute`

---

## 3️⃣ Via l'Interface Graphique (GUI)

Pour utilisateurs préférant le clic et le Drag & Drop. Deux manières de la lancer :

### Mode développement (Tauri dev)

Depuis `anonyfiles_gui` :

```bash
npm run tauri dev
```

La GUI spawne elle-même le sidecar API embarqué — **aucun `uvicorn` à lancer à la main**. Un overlay « Démarrage du moteur NER… » s'affiche pendant ~15-25 s au premier lancement (chargement du modèle spaCy), puis l'UI devient active.

### Application packagée (desktop autonome)

Pour générer un `.app` / `.exe` / `.AppImage` self-contained :

```bash
make desktop
```

Détails de la chaîne de build → voir [`guide_installation_anonyfiles.md`](guide_installation_anonyfiles.md#-application-desktop-autonome).

### Utilisation

- Glissez-déposez un fichier (`.docx`, `.pdf`, `.txt`...)
- Sélectionnez les entités à masquer (ex : `☑ Personnes`, `☑ Emails`)
- Cliquez `Anonymiser`
- Copiez ou sauvegardez le résultat

---

## ⏩ Et ensuite ?

Pour aller plus loin :

- `[[Configuration]]` → Personnaliser les règles (NLP + Regex)
- `[[CLI Reference]]` → Toutes les commandes et options
- `[[API Reference]]` → Intégrer Anonyfiles dans vos workflows Python/Node

