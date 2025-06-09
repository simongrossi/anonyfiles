# 🚀 Guide de déploiement

Ce dossier regroupe les fichiers utiles pour exécuter **Anonyfiles API** en production.

## 📦 Image Docker

Une `Dockerfile` est disponible à la racine du projet. Elle installe les dépendances listées dans `requirements-full.txt` puis lance l'API avec Uvicorn.

```bash
docker build -t anonyfiles .
docker run -p 8000:8000 anonyfiles
```

Pour certains hébergeurs (Heroku, Scalingo...), le `Procfile` fournit la commande de démarrage :

```procfile
web: bash -c 'uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port ${PORT:-8000}'
```

Cette commande nécessite que la variable d'environnement `PORT` soit définie par la plateforme (Railway le fait automatiquement). À défaut, Uvicorn démarrera sur le port `8000`.

## 🛠️ Service systemd

Le fichier [`anonyfiles-api.service`](anonyfiles-api.service) permet de lancer l'API comme service Linux. Exemple d'installation :

```bash
sudo cp deploy/anonyfiles-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now anonyfiles-api.service
```

Les variables d'environnement à définir (dans `/etc/default/anonyfiles-api` par exemple) :

- `ANONYFILES_USER` : utilisateur exécutant le service
- `ANONYFILES_HOME` : chemin du projet
- `ANONYFILES_HOST` : adresse d'écoute (ex. `127.0.0.1`)
- `ANONYFILES_PORT` : port d'écoute (ex. `8000`)
- `ANONYFILES_JOBS_DIR` : répertoire des jobs (défaut `jobs`)

## 📦 Déploiement via Nixpacks

Le fichier `nixpacks.toml` décrit les étapes d'installation et la commande de lancement pour [Nixpacks](https://nixpacks.com/).

```bash
nixpacks build . --name anonyfiles
nixpacks run .
```

Ces commandes créent une image contenant l'API puis la démarrent avec le même ordre que défini dans le `Procfile`. Assurez-vous que la variable `PORT` est disponible dans l'environnement pour que Uvicorn écoute sur le bon port.

## 🚄 Déploiement continu via Railway

Le fichier [`nixpacks.toml`](../nixpacks.toml) est utilisé comme configuration de build
pour le service d'hébergement [Railway](https://railway.app/).
Pour mettre en place un déploiement automatisé :

1. Installer l'outil en ligne de commande Railway :
   ```bash
   npm install -g @railway/cli
   ```
2. Lier le dépôt local au projet Railway existant :
   ```bash
   railway link
   ```
3. Définir les variables d'environnement nécessaires depuis le tableau de bord Railway.
4. Le workflow [`railway.yml`](../.github/workflows/railway.yml) déclenche automatiquement le déploiement à chaque push sur la branche principale.


