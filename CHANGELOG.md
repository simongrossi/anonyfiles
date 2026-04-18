# Changelog

Toutes les modifications notables du projet **Anonyfiles** sont consignées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/) et la gestion sémantique de versions ([semver.org](https://semver.org/lang/fr/)).

---

## [1.4.2] – 2026-04-18

### Corrigé
- **Desktop macOS : `.app` qui ne lançait pas le sidecar depuis Finder** (timeout `API not ready after 60000ms: TypeError: Load failed`). Trois causes conjuguées :
  1. **Signature ad-hoc corrompue** par les fichiers `.DS_Store` créés par Finder dans le dossier `sidecar/` au moindre browse, et par le fait que Tauri ne re-signe pas le bundle après insertion des resources. Fix : post-build hook (`codesign --force --deep --sign -`) dans le `Makefile` et le workflow CI. Le script `build_sidecar.py` supprime aussi les `.DS_Store` avant copie.
  2. **`JOBS_DIR = Path("jobs")` relatif au CWD** : quand le `.app` est lancé depuis Finder, le CWD est `/` (read-only). Le sidecar crashait sur `OSError: [Errno 30] Read-only file system: 'jobs'`. Fix : `core_config.py` lit désormais `ANONYFILES_JOBS_DIR` en priorité, et `main.rs` injecte cette variable pointant vers `app.path().app_data_dir() + "/jobs"` (≈ `~/Library/Application Support/io.anonyfiles.gui/jobs` sur macOS) avant de spawner le sidecar.
  3. L'échec silencieux de ces deux points empêchait tout process enfant d'apparaître — le frontend n'avait aucun /api/health à joindre.

### Vérifié
- End-to-end via `open anonyfiles_gui.app` (équivalent double-clic Finder) : port détecté en 2 s, `/api/health 200 OK`, round-trip anonymisation complet, `jobs/` créé dans le user data dir.

## [1.4.1] – 2026-04-18

### Optimisé
- **Démarrage desktop × 12 plus rapide** : PyInstaller bascule de `--onefile` vers `--onedir`. L'extraction de 120 Mo vers `/tmp` à chaque lancement est éliminée. Temps mesurés sur macOS Apple Silicon (warm start) :
  - Avant (onefile) : /api/health ~12 s
  - Après (onedir) : /api/health ~1 s, cycle anonymisation complet (spaCy inclus) ~3 s
  Premier lancement après installation reste plus long (~30-50 s) à cause du scan Gatekeeper sur les fichiers non signés.
- **Bundle sidecar allégé** : exclusion explicite de `textual`, `rich`, `IPython`, `matplotlib`, `pytest`, `tkinter` (non utilisés côté API). Gain ~15-20 Mo sur le bundle.
- **Option `MODEL` pour le bundle** : `make sidecar MODEL=sm` (ou `make desktop MODEL=sm`) bundle `fr_core_news_sm` (15 Mo) au lieu de `md` (45 Mo). Précision moindre sur noms rares mais chargement encore plus rapide. Défaut `md` inchangé.

### Modifié
- **Tauri `externalBin` → `bundle.resources`** : le sidecar est désormais distribué sous forme de dossier (`src-tauri/sidecar/anonyfiles-api/`) via le système de resources de Tauri 2. Nécessité imposée par le passage à `--onedir`. Le code Rust résout le chemin via `app.path().resolve(..., BaseDirectory::Resource)` et lance le binaire via `tauri_plugin_shell`.
- **Cleanup explicite du sidecar** : `main.rs` tracke le `CommandChild` dans `Mutex<Option>>` et le `kill()` sur `WindowEvent::CloseRequested` + `RunEvent::ExitRequested` pour éviter tout zombie.
- **Capability `shell:allow-execute` retirée** : le sidecar est spawné depuis Rust (setup hook), pas depuis le frontend. Pas besoin de permission côté JS.

## [1.4.0] – 2026-04-18

### Ajouté
- **Desktop autonome** : l'app Tauri embarque désormais l'API FastAPI via un sidecar PyInstaller (`packaging/sidecar/build_sidecar.py`). Le `.app` / `.exe` / `.AppImage` est self-contained — plus besoin de lancer `uvicorn` manuellement.
- **Cibles Makefile** : `make env-pkg`, `make sidecar`, `make desktop` pour builder le bundle desktop en local.
- **CI desktop** : nouveau workflow `.github/workflows/desktop-build.yml` produit des artifacts macOS (ARM+Intel), Windows, Linux sur tag `v*`.
- **Entry point API standalone** : `anonyfiles_api/__main__.py` (`python -m anonyfiles_api --port N`) utilisé par le sidecar.
- **Extras packaging** : `pyproject.toml` expose `[packaging]` (PyInstaller) à côté de `[dev]`.
- **Overlay cold-start** : la GUI affiche « Démarrage du moteur NER… » tant que `/api/health` ne répond pas, pour couvrir les ~15-25 s de chargement spaCy au 1er lancement du sidecar.

### Modifié
- **Tauri 1.6 → Tauri 2** : migration complète (Cargo.toml, tauri.conf.json au nouveau schéma, capabilities scopées, API JS `@tauri-apps/api@2` + plugins `dialog` / `fs` / `clipboard-manager` / `shell`).
- **Découverte de port dynamique** : `main.rs` choisit un port libre via `portpicker` au démarrage et l'expose au frontend via la commande Tauri `get_api_port`. La GUI résout `API_BASE` en async au runtime (via `getApiBase()` dans `src/lib/utils/api.ts`).
- **CORS backend** : ajout de `http://tauri.localhost` et `http://localhost:5173` aux origines par défaut.
- **GUI centralisée** : nouveau `src/lib/utils/api.ts` exporte `apiUrl()`, `pollJob()`, `waitForApiReady()`, `debug()`. Tous les call sites passent par là au lieu d'ad-hoc `fetch`.

### Corrigé
- **GUI / désanonymisation** : URL de polling cassée (template literal contenant du HTML parasite de rendu mathématique dans `src/lib/utils/deanonymize.ts`) et double préfixe `/api/api/` dans `DeAnonymizer.svelte`.
- **GUI / logique Tauri inversée** : `if (isTauri()) throw new Error("Tauri non supporté en mode web")` produisait un crash immédiat en desktop. Retiré.
- **GUI / polling infini** : `while (true)` remplacé par `pollJob()` avec timeout (5 min), backoff exponentiel et respect de `Retry-After` sur HTTP 429.
- **GUI / console.log en prod** : tous les `console.log` / `console.error` gatés derrière `import.meta.env.DEV` (helper `debug()` / `debugError()`).
- **Rust / bug latent** : `main.rs` faisait `mod presets;` alors que le fichier s'appelait `preset.rs`. Compilation Tauri jamais passée côté desktop. Renommé en `presets.rs`.
- **API / config.yaml sous PyInstaller** : le bundle sidecar embarque désormais `anonyfiles_core/config/` (warning `Fichier de configuration YAML non trouvé` éliminé).
- **Code mort supprimé** : `anonyfiles_gui/src/lib/utils/anonyfilesBackend.ts` (jamais importé) et la fonction scaffold `submitAnonymizationRequest` dans `CustomRulesManager.svelte`.
- **.env.example** : réaligné sur `VITE_ANONYFILES_API_URL` (seule variable effectivement lue par le code).

## [1.3.0] – 2026-01-16

### Ajouté
- **Docker Multi-Arch & Sécurité** : Dockerfile réécrit en multi-stage build avec support natif ARM64 (Apple Silicon, NAS) et exécution en utilisateur non-root.
- **Réalisme (Faker)** : Intégration de la librairie `Faker` pour des remplacements réalistes (Noms, Villes, Emails, IBAN...) avec option de cohérence (seed).
- **Validation** : Validation stricte des dates détectées via `dateutil` pour éliminer les faux positifs.
- **Sécurité API** : Gestion fine des origines CORS via variable d'environnement `ANONYFILES_CORS_ORIGINS`.

### Optimisé
- **Gestion des Dépendances** : Abandon des fichiers `requirements.txt` au profit d'une gestion centralisée dans `pyproject.toml` (avec groupe `dev`).
- **Scripts d'Installation** : Modernisation de `Dockerfile`, `Makefile` et `setup_envs.ps1` pour utiliser `pip install .` et garantir la cohérence des versions.
- **Moteur SpaCy** : Utilisation de l'`EntityRuler` pour intégrer les Regex directement dans le pipeline NLP (gain de performance et gestion native des conflits).
- **Frontend** : Configuration Nginx optimisée pour le reverse-proxy API et Dockerfile frontend allégé.
- **API Files** : Utilisation de `mimetypes` standard pour une détection robuste des types MIME.
- **Processors Bureautique** : Support des fichiers Excel multi-onglets (avec préservation des types `str`) et de l'anonymisation récursive dans les tableaux Word.
- **Standardisation des Sorties** : Harmonisation de tous les remplacements (PER, LOC, ARG, DATE...) vers le format unique indexé `{{TAG_001}}` pour une meilleure réversibilité.
- **Sécurité Infra** : API isolée du réseau public (port 8000 non exposé, routage interne uniquement) et code source monté en lecture seule (`:ro`) pour empêcher toute persistance.
- **Reverse Proxy Sécurisé** : Configuration Nginx durcie avec headers de sécurité (X-Forwarded-For, Proto) et point d'entrée unique sur :3000.
- **Audit CI Automatisé** : Ajout de `pip-audit` dans le pipeline GitHub Actions pour bloquer le build en cas de détection de CVEs connues dans les dépendances.
- **Audit CI Automatisé** : Ajout de `pip-audit` dans le pipeline GitHub Actions pour bloquer le build en cas de détection de CVEs connues dans les dépendances.
- **Sécurité Locale** : L'exécution directe de l'API (`python api.py`) écoute désormais par défaut sur `127.0.0.1` pour éviter l'exposition accidentelle sur le réseau local.
- **Pipeline CI/CD Complet** : Workflow GitHub Actions incluant Tests (Python 3.11), Linting (Ruff), Formatage (Black), Audit Sécurité (Bandit/Safety/Pip-audit), Build (Wheel) et Publication Docker automatique sur tags.

### Corrigé
- **Docker Build** : Résolution de `ModuleNotFoundError: No module named 'pydantic_settings'` et des problèmes d'installation en mode éditable avec Hot-Reload.
- **Frontend Docker** : Correction des chemins Nginx (`/api/`) et de la configuration `API_URL` codée en dur pour compatibilité Synology/Reverse-Proxy.
- **API Configuration** : Correction critique du chargement du `config.yaml` dans Docker via `ANONYFILES_CONFIG_PATH` et refonte complète via Pydantic `BaseSettings`.
- **CLI** : Ajout de la commande `anonyfiles-cli logs interactive` (TUI avec Textual) pour la consultation avancée des logs.
- **Documentation et Alias** : Unification des commandes CLI (`anonyfiles-cli`), ajout de `config init`, et mise à jour massive des READMEs.
- **Refactoring** : Nettoyage du code, suppression des `if/elif` géants pour les MIME types et les regex, adoption du pattern Registry pour les générateurs (`replacer.py`).
- **Robustesse API** : Ajout d'un gestionnaire global d'exceptions (500) pour ne plus fuiter les stacktraces au client et garantir des réponses JSON propres.
- **Documentation** : Synchronisation complète des README et CHANGELOG avec les dernières évolutions techniques (Docker, Faker, Sécurité).
- **Sécurité du Code** : Correction des vulnérabilités remontées par Bandit (MD5 hashing explicite, protection contre l'injection shell, gestion des chemins temporaires).
- **Qualité du Code** : Mise en conformité stricte avec `black` et `ruff` sur l'ensemble du codebase.

## [1.2.1] – 2025-06-08

### Corrigé
- La reconstruction des paragraphes dans les documents Word préserve désormais la mise en forme des runs (et traite les tableaux).

## [1.2.0] – 2025-06-03

### Ajouté
- Affichage du nombre de lignes/caractères pour les zones de texte dans la GUI (meilleur feedback utilisateur)
- Mode sombre pour la GUI
- Export direct du mapping CSV après anonymisation
- Option `--append-timestamp` pour organiser les fichiers de sortie par session/timestamp
- Endpoints API pour suppression de jobs (backend + intégration GUI)
- Bouton "Supprimer les fichiers du job" dans la GUI
- Notification visuelle à l'utilisateur (composant NotificationDisplay.svelte)
- Refonte du layout principal pour un affichage desktop plus pro : Header fixe, menu burger mobile, sidebar responsive
- Correction du bug de logo en double sur mobile

### Modifié
- Refactorisation avancée du backend API : modularisation, centralisation configuration, gestion robuste de la config et du logger, refonte organisation fichiers (`anonyfiles_api/routers/`, etc.)
- Refactorisation du moteur d’anonymisation (standardisation du flux, application universelle des règles custom, amélioration du Replacer)
- Facto gestion fichiers de sortie, centralisation logging, harmonisation CLI/API (timestamp, sous-dossiers, cohérence mapping/output/log)
- Refactoring des stores et de la gestion des fichiers dans la GUI (modularité, abonnements Svelte, lazy loading, stores globaux)
- Factorisation et nettoyage de la logique GUI (DataAnonymizer.svelte, FileDropZone, etc.), amélioration responsive

### Corrigé
- Fix NotImplementedError dans le CsvProcessor (implémentation de `reconstruct_and_write_anonymized_file`)
- Résolution de NameError sur `original_input_path` dans le backend
- Résolution d’erreurs TypeScript, Svelte, Vite/Rollup dans la GUI
- Sécurisation de l’API : validation UUID, nommage safe à l’upload, gestion d’erreurs JSON
- Correction bugs sur la prévisualisation CSV et gestion accents/encodage
- Correction de la gestion des entités exclues (CLI et GUI)

---

## [1.1.0] – 2025-05-31

### Ajouté
- Support natif des fichiers JSON, PDF
- Composant CustomRulesManager pour la gestion centralisée des règles personnalisées (GUI)
- Ajout du support des règles de remplacement personnalisées dans la CLI et la GUI (store global, log détaillé)
- Option --force sur la CLI pour écraser explicitement les fichiers existants
- Génération automatique du mapping CSV lors de l’anonymisation, utilisable pour la désanonymisation
- Système d’audit log détaillé pour chaque anonymisation (affiché dans la GUI)

### Modifié
- Refonte du core métier (BaseProcessor, factorisation processors/pipeline, extraction/remplacement universel)
- Standardisation de la logique d’anonymisation et de désanonymisation (pipeline factorisé)
- UI modernisée : toggles, meilleure accessibilité, layout amélioré
- Documentation enrichie sur le workflow, la configuration YAML, la désanonymisation
- Refactorisation avancée du logging (centralisation via run_logger.py)

### Corrigé
- Correction de bugs d’affichage dans la GUI
- Correction du mapping lors de l’anonymisation des fichiers XLSX/CSV
- Résolution d’erreurs d’importation circulaire dans l’API
- Correction du parsing Svelte (balises, props, events, etc.)
- Correction de l’envoi du paramètre `has_header` pour CSV/XLSX

---

## [1.0.0] – 2025-05-21

### Ajouté
- Première version stable du projet :  
  - **CLI** (Typer) : anonymisation/désanonymisation, export mapping, configuration YAML, audit log
  - **API** (FastAPI) : endpoints REST, jobs asynchrones, gestion fichiers par UUID, audit log, endpoints dédiés pour mapping/output/log
  - **GUI** (Tauri + Svelte) : interface drag&drop, preview TXT/CSV/XLSX, onglets résultat, logs audit, gestion des règles personnalisées, désanonymisation via mapping
- Support des formats .txt, .csv, .docx, .xlsx
- Application des règles personnalisées et exclusion des entités sélectionnées
- Export et import de mapping pour la désanonymisation
- Mode desktop/mobile responsive, actions "Copier", "Exporter" sur les résultats
- Gestion des jobs, statuts, suppression automatique après chaque appel API

### Modifié
- Refonte ergonomique et visuelle complète de la GUI
- Mise à jour et enrichissement des README (généraux, CLI, GUI, API)
- Uniformisation du nommage des dossiers/fichiers pour harmonisation CLI/API

### Corrigé
- Correction de l’exclusion correcte des entités via l’option CLI et GUI
- Résolution de plusieurs bugs dans l’import/export CSV, audit log, preview
- Correction de l’application des règles custom avant spaCy (priorité garantie)
- Sécurisation de l’API contre les injections de chemin et noms de fichiers

---

## [0.9.0] – 2025-05-07

### Ajouté
- Première version CLI, support multi-format, anonymisation brute
- Prise en charge du remplacement indexé sur TXT, DOCX, CSV, XLSX
- Mapping des entités PER avec codes séquentiels (ex : NOM001)
- Gestion de la configuration YAML, options avancées pour chaque type d’entité

---

> _Ce changelog est généré automatiquement à partir de l’historique des commits (synthétisé et regroupé par version). Pour plus de détails, voir l’historique Git complet._
