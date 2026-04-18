# Guide d'Installation

Anonyfiles est conçu pour être modulaire. Vous pouvez l'installer de plusieurs façons selon vos besoins :

1. **Docker** : Pour tester l'API sans rien installer sur votre machine.
2. **Standard (Pip)** : Pour utiliser la CLI ou développer (Python).
3. **Interface Graphique (GUI) en dev** : Tauri dev, depuis les sources.
4. **Application desktop autonome** : `.app` / `.exe` / `.AppImage` self-contained (embarque l'API en sidecar).

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

Le projet utilise `pyproject.toml` (setuptools) comme source unique de vérité pour les dépendances.

```bash
pip install -e .
```

Extras disponibles :

- `pip install -e ".[dev]"` — pytest, ruff, black, bandit, safety, pip-audit (pour les contributeurs)
- `pip install -e ".[packaging]"` — PyInstaller (pour builder le sidecar desktop)

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

## 🖥️ Installation de l'Interface Graphique (GUI) — mode développement

Cette section est pour contribuer à la GUI ou la lancer en mode dev. Pour une app packagée prête à distribuer, voir la section suivante.

### Prérequis GUI

- Node.js 20+ & npm
- Rust stable & Cargo ([rustup](https://rustup.rs/))
- Les dépendances Python + le modèle spaCy installés (voir installation standard ci-dessus) — la GUI va spawner l'API en sidecar, qui n'existe encore que comme venv Python à ce stade.

### Installation et Lancement

```bash
cd anonyfiles_gui
npm install
npm run tauri dev
```

L'app Tauri spawne elle-même le binaire sidecar au démarrage. Pour que ça marche en dev, il faut **que le sidecar ait été buildé au moins une fois** — voir section suivante. Si `src-tauri/binaries/anonyfiles-api-<votre-triple>` n'existe pas, Tauri affiche une erreur au lancement.

Alternative si tu ne veux pas builder le sidecar : lance `uvicorn anonyfiles_api.api:app --port 8000` à côté et pointe `VITE_ANONYFILES_API_URL=http://127.0.0.1:8000` — la GUI détecte qu'elle tourne en web et utilise cette URL.

---

## 📦 Application desktop autonome

Cette section produit un `.app` (macOS) / `.exe` ou `.msi` (Windows) / `.AppImage` ou `.deb` (Linux) qui contient **tout** (GUI + moteur NLP + modèle spaCy + API). L'utilisateur final n'a rien à installer.

### Prérequis build

- Node.js 20+, Rust stable, Python 3.11+
- Sous Linux : `libwebkit2gtk-4.1-dev`, `libssl-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`, `libgtk-3-dev`, `build-essential`, `curl`, `wget`, `file` (voir `.github/workflows/desktop-build.yml` pour la liste exacte)

### Build via Makefile (recommandé)

```bash
make desktop                   # modèle md (précision max, ~45 Mo de modèle)
make desktop MODEL=sm          # modèle sm (bundle ~30 Mo plus léger)
```

Sous le capot :

1. `make env-pkg` crée `env-pkg/` (venv Python 3.11+) et installe `anonyfiles[packaging]` + le modèle `fr_core_news_<MODEL>`
2. `make sidecar` lance `python packaging/sidecar/build_sidecar.py --model $(MODEL)` qui appelle PyInstaller en mode **`--onedir`** et dépose le dossier `anonyfiles-api/` dans `anonyfiles_gui/src-tauri/sidecar/`
3. `cd anonyfiles_gui && npm install && npm run tauri build` produit le bundle final, qui embarque le sidecar via `bundle.resources`

Pour cibler un Python spécifique : `make env-pkg PYTHON=/opt/homebrew/bin/python3.12`.

**Pourquoi `--onedir` et pas `--onefile` ?** onefile extrait ~120 Mo dans `/tmp` à chaque lancement (≈20-30 s de cold start). onedir décompresse une fois à l'installation et démarre ensuite en ~1 s (mesuré sur macOS Apple Silicon).

### Sorties

Tout dans `anonyfiles_gui/src-tauri/target/release/bundle/` :

| Plateforme | Fichiers |
|---|---|
| macOS | `macos/anonyfiles_gui.app`, `dmg/anonyfiles_gui_<version>_<arch>.dmg` |
| Windows | `msi/anonyfiles_gui_<version>_<arch>_en-US.msi`, `nsis/anonyfiles_gui_<version>_<arch>-setup.exe` |
| Linux | `appimage/anonyfiles_gui_<version>_<arch>.AppImage`, `deb/anonyfiles_gui_<version>_<arch>.deb` |

Taille ~500-550 Mo dossier décompressé (onedir). Cold start **~1-3 s en warm** (2e lancement et suivants), premier lancement après installation plus long (~30-50 s sur macOS à cause du scan Gatekeeper sur binaires non signés — voir section signature).

### CI / release

Pousser un tag `v*` sur GitHub déclenche le workflow `desktop-build.yml` qui produit les 4 artifacts (macOS ARM, macOS Intel, Windows, Linux) et les attache à la release. Le workflow `ci.yml` (tests + wheel Python + image Docker) reste déclenché indépendamment.

### Signature de code (non inclus)

Les binaires produits sont **non signés**. Au premier lancement :
- macOS : Gatekeeper affiche « développeur non identifié » → clic droit → Ouvrir
- Windows : SmartScreen affiche un avertissement → « Informations supplémentaires » → « Exécuter quand même »

Pour une distribution publique, il faut un Apple Developer ID ($99/an) + notarisation macOS, et un certificat EV code signing Windows (~$300/an). Hors scope de ce guide.

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

Builder le sidecar desktop puis l'app Tauri :

```bash
make desktop
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
