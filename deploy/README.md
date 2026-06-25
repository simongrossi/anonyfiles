# 🚀 Guide de déploiement

Ce dossier regroupe les fichiers utiles pour exécuter **Anonyfiles API** en production.

## 📦 Image Docker

Une `Dockerfile` est disponible à la racine du projet. Elle utilise Python 3.11,
installe les dépendances verrouillées dans `requirements.txt`, installe ensuite
le package depuis `pyproject.toml` sans relancer la résolution, puis lance l'API
avec Uvicorn.

```bash
docker build -t anonyfiles .
docker run -p 8000:8000 anonyfiles
```

Pour certains hébergeurs (Heroku, Scalingo...), le `Procfile` fournit la commande de démarrage :

```procfile
web: uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port ${PORT:-8000}
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
- `ANONYFILES_MAX_UPLOAD_SIZE_MB` : taille max d'un fichier téléversé en Mio (défaut `100`)
- `ANONYFILES_JOB_RETENTION_HOURS` : conservation des jobs avant purge auto, en heures (défaut `24`, `0`=désactivé)
- `ANONYFILES_JOB_PURGE_INTERVAL_MINUTES` : intervalle de balayage de purge (défaut `60`)
- `ANONYFILES_CORS_ORIGINS` : origines autorisées CORS (séparées par des virgules)
- `ANONYFILES_API_KEY` : clé API optionnelle. Si définie, les endpoints de
  traitement exigent `X-API-Key: <clé>` ou `Authorization: Bearer <clé>`.

Les endpoints `/`, `/health`, `/health/spacy`, `/docs` et `/openapi.json`
restent publics pour le monitoring et la découverte. Les uploads, statuts de
jobs, téléchargements de fichiers, annulations/suppressions et WebSocket de
statut sont protégés lorsque `ANONYFILES_API_KEY` est non vide.

## 📦 Déploiement via Nixpacks

Le fichier `nixpacks.toml` décrit les étapes d'installation et la commande de lancement pour [Nixpacks](https://nixpacks.com/).
Il suit la même stratégie que l'image Docker : `requirements.txt` pour les
versions exactes, puis `pip install --no-deps .` pour installer le package local.

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
