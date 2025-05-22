FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONPATH=/app/anonyfiles-cli

WORKDIR /app

# Copier tout le projet dans le conteneur
COPY . /app

# Installer pip et dépendances
RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r anonyfiles_api/requirements.txt

# Exposer le port utilisé par uvicorn
EXPOSE 8000

# Commande de démarrage de l'application
CMD ["uvicorn", "anonyfiles_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
