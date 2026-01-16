# Guide d'Installation

Anonyfiles est conçu pour être modulaire. Vous pouvez l'installer de plusieurs façons selon vos besoins :

1. **Docker** : Pour tester l'API sans rien installer sur votre machine.
2. **Standard (Pip)** : Pour utiliser la CLI ou développer (Python).
3. **Interface Graphique (GUI)** : Pour une utilisation bureautique (Desktop).

---

## 🐳 Méthode Rapide : Docker (API)

C'est la méthode la plus simple pour lancer l'API REST sans gérer les dépendances Python.

### Lancement en une commande

Exécutez cette commande dans votre terminal à la racine du projet :

```bash
docker build -t anonyfiles . && docker run -p 8000:8000 anonyfiles
```

Une fois le conteneur lancé, accédez à :

- Documentation API (Swagger) : http://localhost:8000/docs
- API Root : http://localhost:8000

---

## 🛠️ Installation Standard (CLI & Core)

Cette méthode installe le cœur (anonyfiles_core) et l'outil en ligne de commande (anonyfiles_cli).

### 1. Prérequis

- Python 3.11+ (Recommandé).
- pip (Gestionnaire de paquets Python).
- (Optionnel) venv pour isoler l'environnement.

### 2. Clonage du projet

```bash
git clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles
```

### 3. Installation des dépendances

Vous pouvez installer le projet avec les dépendances figées (recommandé) :

```bash
pip install -r requirements.txt
```

(Le fichier requirements.txt à la racine installe tout le nécessaire pour le Core, la CLI et l'API).

### 4. Téléchargement du modèle de langue (Indispensable)

Anonyfiles utilise spaCy pour la reconnaissance d'entités (NER). Vous devez télécharger le modèle français :

```bash
python -m spacy download fr_core_news_md
```

### 5. Vérification

Vérifiez que la CLI fonctionne :

```bash
anonyfiles-cli --help
```

---

## 🖥️ Installation de l'Interface Graphique (GUI)

L'interface graphique nécessite des outils supplémentaires pour être compilée (Rust et Node.js).

### Prérequis GUI

- Node.js (v18+) & npm.
- Rust & Cargo (Voir guide d'installation Rust).
- La CLI Python doit être installée et accessible dans le PATH.

### Installation et Lancement

Allez dans le dossier de la GUI :

```bash
cd anonyfiles_gui
```

Installez les dépendances JavaScript :

```bash
npm install
```

Lancez l'application en mode développement :

```bash
npm run tauri dev
```

---

## ⚙️ Scripts d'Automatisation (Environnements de Dev)

Pour les développeurs, des scripts permettent de créer des environnements virtuels isolés (env-cli, env-api, env-gui).

### 🐧 Linux / macOS (Makefile)

Utilisez le Makefile à la racine :

Installation complète (setup) :

```bash
make setup
```

Lancer l'API :

```bash
make api
```

Lancer un test CLI :

```bash
make cli
```

Note Debian/Ubuntu : Si nécessaire, lancez `sudo make install-deps-debian` pour installer les paquets système manquants.

### 🪟 Windows (PowerShell)

Utilisez le script anonyfiles.ps1 à la racine :

Installation (Setup) :

```powershell
./anonyfiles.ps1 -action setup
```

Lancer l'API :

```powershell
./anonyfiles.ps1 -action api
```

Lancer la CLI :

```powershell
./anonyfiles.ps1 -action cli
```

---

## 📦 Déploiement API (Production)

Pour déployer l'API sur un serveur, consultez le dossier deploy/.

### Service Systemd (Linux)

Un exemple deploy/anonyfiles-api.service est fourni.

- Copiez-le dans /etc/systemd/system/.
- Configurez les variables (User, Chemins).
- Activez le service : `systemctl enable --now anonyfiles-api`.

### Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| ANONYFILES_JOBS_DIR | Dossier des jobs | jobs/ |
| ANONYFILES_CORS_ORIGINS | Origines autorisées | — |
