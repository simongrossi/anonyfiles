FROM python:3.11-slim

WORKDIR /app

# AJOUT CRITIQUE : Installation de gcc et des outils de build pour l'architecture ARM
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Installation des dépendances Python
RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "anonyfiles_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
