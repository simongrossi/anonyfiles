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

Pour utilisateurs préférant le clic et le Drag & Drop.

### Lancement

Depuis `anonyfiles_gui` :

```bash
npm run tauri dev
```

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

