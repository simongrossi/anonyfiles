# anonyfiles/Dockerfile

# Étape 1 : Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Installation des dépendances système nécessaires uniquement pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Création du virtualenv et installation des libs
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copie des fichiers de dépendances uniquement
COPY requirements.txt .
# S'assurer que le package soit installable aussi (si besoin de dépendances internes)
# Mais ici on installe d'abord requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt
# Si vous devez télécharger le modèle spacy ici pour qu'il soit dans l'image :
# RUN python -m spacy download fr_core_news_md

# Étape 2 : Image finale (Runtime)
FROM python:3.11-slim

WORKDIR /app

# Création d'un utilisateur non-root
RUN groupadd -r anonyfiles && useradd -r -g anonyfiles anonyfiles

# Copie de l'environnement virtuel depuis le builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copie du code
COPY . /app
# Gestion des permissions
RUN chown -R anonyfiles:anonyfiles /app

# Bascule sur l'utilisateur sécurisé
USER anonyfiles

EXPOSE 8000

# Utilisation directe du chemin venv
CMD ["uvicorn", "anonyfiles_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
