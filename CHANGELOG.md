# Changelog

Toutes les modifications notables du projet **Anonyfiles** sont consignées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/) et la gestion sémantique de versions ([semver.org](https://semver.org/lang/fr/)).

---

## [1.2.1] – 2025-06-08

### Corrigé
- La reconstruction des paragraphes dans les documents Word préserve désormais la mise en forme des runs

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
