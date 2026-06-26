# Roadmap & audit technique — Anonyfiles

> Document de suivi créé le **2026-06-25**. Objectif : centraliser l'audit
> (documentation + dépendances) et le plan d'action priorisé, pour pouvoir
> reprendre le travail plus tard. Cocher les cases au fur et à mesure.

---

## 0. Contexte / travail déjà réalisé

**Mise à jour 2026-06-25** : toutes les branches sont désormais **mergées dans `main`**
(fast-forward). Le fix engine `_sanitize_for_ner` (`claude/flamboyant-torvalds`) est
déjà présent dans `main` (intégré + reformaté black). La **Phase 0** (modernisation déps)
a été réalisée par le commit `Modernize Python dependency stack`.

| Branche | Contenu | État |
|---|---|---|
| `fix/docx-upload-and-anonymization` | Fix issue #73 + durcissement docx + fix mismatch Excel + tests GUI Vitest + docs | ✅ mergée dans `main` |
| `feat/job-retention` | Purge automatique des jobs expirés (TTL, env `ANONYFILES_JOB_RETENTION_HOURS`) | ✅ mergée dans `main` |
| `claude/flamboyant-torvalds` | `_sanitize_for_ner` (tokens custom rules avant NER) | ✅ déjà dans `main` |
| commit `Modernize Python dependency stack` | Unification déps + spaCy 3.8/NumPy 2/pandas + lock unique + fix nixpacks + nettoyage | ✅ sur `main` |

> ✅ **Validation locale effectuée** : stack Python 3.11, `numpy 2.4.6`,
> `pandas 3.0.3`, `spacy 3.8.14`, modèle `fr_core_news_md 3.8.0`,
> `pytest -q tests` vert (`47 passed, 2 skipped`).

---

## 1. Audit documentation (`.md`)

**Problème central : trois récits contradictoires sur la gestion des dépendances**,
et des fichiers référencés qui n'existent pas.

- [x] **🔴 `CONTRIBUTING.md` (l.11, 49, 76-84)** : référence `pip install -r requirements-test.txt`
  et `pip-compile pyproject.toml -o requirements.txt` — ces `.txt` **n'existent pas**.
- [x] **🔴 `deploy/README.md` (l.7)** : prétend que le Dockerfile installe `requirements-full.txt`
  (faux : il fait `pip install .`) et ce fichier est **manquant**.
- [x] **🔴 `nixpacks.toml`** : `pip install -r requirements-full.txt` → fichier absent →
  **déploiement Railway/nixpacks cassé**.
- [x] **🟠 `anonyfiles_core/README.md` (l.17)** : « Chaque module possède son `requirements.txt` »
  → contredit la centralisation `pyproject.toml`.
- [x] **🟠 `anonyfiles_cli/README.anonyfiles_cli.md` (l.48)** : `pip install -r requirements.txt`
  alors que ce fichier est un stub « obsolète ».
- [x] **🟠 `anonyfiles_gui/README.anonyfiles_gui.md` (l.26)** : exige **Python 3.9+** alors que
  tout le reste (et `pyproject`) exige **3.11+**.
- [x] **🟠 `README.md` (l.439) + `CHANGELOG.md`** : « Plus de `requirements.txt` ! » contredit
  `CONTRIBUTING.md` et l'existence de `requirements.in`.

> Les docs **fonctionnelles** (formats `.docx/.pdf/.json/.xlsx`, modèle spaCy, quickstart)
> sont à jour et cohérentes.

---

## 2. Audit dépendances — racine des conflits historiques

### 4 sources de dépendances qui se contredisent

| Source | spaCy | numpy | pandas | fastapi |
|---|---|---|---|---|
| `pyproject.toml` (canonique) | `>=3.7,<4.0` | `>=1.26` | `>=2.0` | `>=0.115.6` |
| `requirements.in` | **`>=3.7,<3.8`** | `>=1.23.5` | `>=1.5` | (libre) |
| `requirements-test.in` | **`>=3.7,<3.8`** | **`~=1.26`** | `>=1.5` | (libre) |
| `anonyfiles_api/requirements.txt` | **`==3.7.5`** | `>=1.23.5` | `>=1.5` | **`==0.111.0`** |

### Cause profonde du blocage

Les **URLs de modèles spaCy sont épinglées en `3.7.0`** (`requirements.in` :
`fr_core_news_sm/md-3.7.0`). Ces modèles **exigent spaCy 3.7.x**, ce qui enchaîne tout :

```
modèle 3.7.0  →  spaCy <3.8  →  numpy <2  →  pandas/thinc anciens
```

**spaCy 3.8 est la version qui a débloqué NumPy 2.x.** Tant qu'on reste sur les modèles 3.7.0,
on est coincé sur numpy 1.26 et un écosystème daté.

**Instabilité selon le chemin d'installation :**
- `pip install .` (Docker, CI) → résout vers spaCy **3.8** + numpy 2 (moderne)
- `pip-sync requirements.in` / nixpacks → force spaCy **3.7** + numpy 1.26 (ancien)

→ C'est l'origine du « obligé de mettre des versions non récentes / conflits ».

### Sommes-nous à jour ? (versions connues début 2026)

| Paquet | Projet | Dernière | Verdict |
|---|---|---|---|
| spaCy | couplé 3.7.0 (via modèles) | 3.8.x | 🔴 bloqué une mineure en arrière |
| numpy | forcé 1.26 | 2.x | 🔴 un **majeur** en retard (à cause de spaCy 3.7) |
| pandas | 1.5 / 2.0 selon source | 2.2.x | 🟠 incohérent |
| FastAPI | 0.111 *et* 0.115 | ~0.118 | 🟠 conflit interne |
| pydantic | v2 mais `class Config` (v1-style) | 2.x | 🟡 warnings de dépréciation |
| Tauri / Rust | v2 | v2 | ✅ à jour |
| Svelte | 4.2 | 5.x | 🟠 un majeur en retard |
| Vite | 4.5 | 6/7 | 🟠 deux majeurs en retard |
| Tailwind | 3.4 | 4.x | 🟠 un majeur en retard |

---

## 3. Plan d'action priorisé

### Phase 0 — Déblocage déps Python (impact le plus élevé)
- [x] Bumper les **modèles spaCy → 3.8.0** + `spacy>=3.8,<3.9`, lever le plafond numpy
      (`>=1.26` autorise 2.x), pandas `>=2.2`.
- [x] **Une seule source de vérité** : garder `pyproject.toml`, supprimer/aligner
      `requirements.in`, `requirements-test.in`, `anonyfiles_api/requirements.txt`
      (retirer les pins `fastapi==0.111`, `spacy==3.7.5`).
- [x] Régénérer **et commiter** un lock unique (`pip-compile pyproject.toml`) **ou** assumer
      100 % pyproject. Créer le `requirements-full.txt` manquant **ou** corriger
      `nixpacks.toml` en `pip install .` (déploiement actuellement cassé).
- [x] Valider : `pip install .` + `python -m spacy download fr_core_news_md` + suite de tests
      verte **sous numpy 2**.

### Phase 1 — Cohérence doc (rapide, juste après Phase 0)
- [x] Corriger CONTRIBUTING / `deploy/README` / `core/README` / cli README / gui README
      (Python 3.11, vraie stratégie de déps). Tout doit raconter **la même** histoire.

### Phase 2 — Dette technique ciblée
- [x] Pydantic v2 : `class Config` → `ConfigDict` (supprime les warnings).
- [x] Nettoyer le smell de `spacy_engine.py` : suppression de `_active_spacy_module` et des
      gardes `getattr/hasattr` ; le code utilise `spacy.util.is_package` / `spacy.load` /
      `self.nlp.pipe_names` directement. Les stubs de test ont été rendus complets
      (`util.is_package` + `pipe_names`/`add_pipe`) et les stubs `sys.modules["spacy"]`
      obsolètes retirés (spaCy est une dépendance dure). Validé : suite complète **78 passed**
      sur Python 3.11 + modèle réel (dont `test_full_flow`), mypy/ruff/black OK.
- [x] Supprimer les méthodes `replace_entities` legacy restantes (pdf/excel/json) — mortes.
- [x] Corriger la ligne dupliquée `anonyfiles_api/routers/anonymization.py:132`.
- [x] Retirer les fichiers parasites versionnés : `debug_job_mock.py`, `input.txt`,
      `input_test.txt`, `validate_fix_final.py`.

### Phase 3 — Modernisation front (chantiers séparés, un par un) — ✅ TERMINÉE
- [x] Vite 4 → **6** (via étapes : 5 d'abord avec plugin-svelte 3, puis 6 avec le couple
      Svelte 5 / plugin-svelte 5). Étape `Build (Vite)` ajoutée à la CI.
- [x] Svelte 4 → **5** (mode legacy : composants non réécrits en runes pour l'instant).
      `main.ts` → API `mount()`, `svelte.config.js` → `vitePreprocess` (svelte-preprocess retiré),
      `lucide-svelte` 0.469 → 1.x avec remap des icônes retirées (`Github`→`ExternalLink`,
      `Loader2`→`LoaderCircle`). Build/tsc/vitest verts + **smoke test visuel OK**.
- [x] Tailwind 3 → **4** : migration via l'outil officiel (`@theme` CSS-first, `@plugin`,
      `@custom-variant dark`, couche de compat couleur de bordure, renames d'utilitaires),
      PostCSS `@tailwindcss/postcss`, suppression du `tailwind.config.cjs` mort. Smoke test visuel OK.

### Phase 3+ — Migration runes Svelte 5 (optionnel, EN COURS)

> **Reprise : c'est ici qu'on s'est arrêté.** Le mode legacy fonctionne parfaitement
> (non déprécié), donc cette migration est de la modernisation, pas une urgence.

**Méthode validée** (recette à réappliquer pour chaque composant) :
1. `export let x` → `let { x = défaut } = $props();`
2. `let y = …` (état réactif local) → `let y = $state(…);` — **attention : en mode runes,
   TOUT état réactif local doit passer en `$state`, sinon réactivité silencieusement cassée.**
3. `$:` dérivé pur → `$derived(…)` ; `$:` à effet de bord → `$effect(() => { … })`
4. `createEventDispatcher` : fonctionne encore en mode runes → on peut le **garder** d'abord
   (parent inchangé), et convertir en *callback props* dans un second temps.
5. Vérifier : `npm run build` + `npx tsc --noEmit` + **test d'interaction réel**
   (preview_eval : cliquer/saisir et constater la mise à jour) + screenshot.

> Alternative recommandée : `cd anonyfiles_gui && npx sv migrate svelte-5` dans un **vrai terminal**
> (l'outil officiel est interactif/clack — non pilotable depuis l'agent), puis relire le diff + tester.

**Avancement : ✅ les 14 composants migrés en runes** (build + tsc + tests d'interaction réels :
nav, toggle thème dark/light, `bind:selected` enfant→parent, compteur de saisie via `$effect`).
- [x] `Sidebar.svelte` (POC)
- [x] `ToggleButton.svelte`, `SwitchTheme.svelte`
- [x] `FileDropZone.svelte` (createEventDispatcher conservé)
- [x] `Header.svelte`, `CsvPreview.svelte`, `XlsxPreview.svelte`, `AuditLogTable.svelte`
- [x] `LogView.svelte`, `ConfigurationView.svelte`, `ExportDirectoryChooser.svelte`, `ResultView.svelte`
- [x] `AnonymizationOptions.svelte` (`selected` en `$bindable()`)
- [x] `DataAnonymizer.svelte`
- [ ] (bonus, optionnel) remplacer `createEventDispatcher` par des callback props dans
      `FileDropZone` et `DataAnonymizer` (seul reliquat ; non urgent, ça marche en l'état)

### Phase 4 — Sécurité / robustesse
- [x] Merger les branches en cours (`fix/docx…`, `feat/job-retention`) + pousser/PR.
- [x] Auth optionnelle sur l'API (clé API activable par `ANONYFILES_API_KEY`)
      pour les déploiements publics : endpoints de traitement protégés par
      `X-API-Key` ou `Authorization: Bearer`, santé/docs publiques, support GUI
      opt-in via `VITE_ANONYFILES_API_KEY`.

### Phase 5 — Robustesse moteur / confiance anonymisation
- [x] **Redaction PDF sûre** : redaction basée sur les coordonnées du texte original
      avec suppression vérifiée du texte sensible extractible du PDF final.
- [x] **Corpus qualité anonymisation** : fixtures réalistes avec résultats attendus
      dans `tests/quality/corpus/anonymization_cases.json` et runner dédié
      couvrant noms, emails, téléphones, IBAN, dates, adresses, organisations
      et faux positifs stables.
- [x] **Tests golden par format** : snapshots attendus pour TXT/CSV/DOCX/XLSX/PDF/JSON afin de
      sécuriser la reconstruction, la lisibilité des sorties et l'absence de fuites
      ou corruptions silencieuses.
- [x] **Meilleure gestion des modèles spaCy** : helper partagé, commande
      `anonyfiles-cli utils spacy-status`, endpoint `/health/spacy` et bloc
      `spacy` de `/health` indiquant modèle installé, version, compatibilité spaCy
      et instructions d'installation/réparation.
- [x] **Typage progressif du core** : `mypy` introduit dans les dépendances dev
      avec une cible progressive configurée dans `pyproject.toml` sur les types
      partagés, les processors formats, la factory et le writer.

### Phase 6 — Jobs API / exploitation
- [x] **Vraie file de jobs API** : `BackgroundTasks` FastAPI remplacé par une file interne
      avec workers, statuts persistants enrichis, annulation, retry, timeouts, progression
      par phase, arrêt propre et endpoints `/jobs/queue` + `/jobs/{job_id}/cancel`.
- [x] **Lifecycle FastAPI moderne** : `@app.on_event(...)` remplacé par `lifespan`;
      les workers de jobs et la tâche de purge démarrent/s'arrêtent proprement.
- [x] **Observabilité structurée** : `status.json` et les logs `job_event` exposent
      durée par étape, taille fichier, nombre d'entités, type de sortie, statut final
      et erreurs catégorisées.

### Phase 7 — Produit / UX
- [x] **Profils d'anonymisation** : presets (`strict RGPD`, `léger`,
      `documents RH`, `contrats`, `logs techniques`) au-dessus des options
      détaillées dans la GUI, avec options manuelles toujours modifiables et
      retour automatique en mode personnalisé.
- [x] **Prévisualisation des entités détectées** : endpoint
      `/anonymize_preview/` en dry-run, tableau GUI avant traitement final,
      possibilité de décocher une entité ou corriger son label, puis lancement
      de l'anonymisation avec décisions exactes par texte détecté.
- [ ] **Batch complet** : traitement multi-fichiers avec rapport global, erreurs par fichier,
      ZIP final et reprise possible.

### Phase 8 — Priorité P0 : fiabilité de l'anonymisation

> État post-déploiement 2026-06-26 : serveur public fonctionnel, CI verte,
> correction mobile du menu résultat déployée, et correction de détection des
> prénoms isolés (`Pierre`, `Ambre`) validée en local + production.

> Principe produit : pour les utilisateurs, le risque majeur n'est pas une UX
> imparfaite, mais une donnée sensible qui reste visible alors que le résultat
> est présenté comme anonymisé. La prochaine priorité est donc la réduction des
> fuites avant l'ajout de gros workflows comme le batch complet.

#### P0.1 — Scanner anti-fuite sur tous les formats

- [x] **Tous les formats principaux** : tests de bout en bout via
      `AnonyfilesEngine` sur sorties `.txt`, `.csv`, `.json`, `.docx`, `.xlsx`
      et `.pdf`, avec extraction/relecture du fichier final, scan des valeurs
      sensibles attendues et conservation des faux positifs publics
      (`SIREN-2026`, `EMAIL-2026`, etc.).
- [x] **DOCX** : extraire le texte du `.docx` anonymisé final (paragraphes,
      tableaux, en-têtes/pieds) et échouer si une valeur sensible attendue reste.
- [x] **PDF** : extraire le texte du PDF anonymisé final et vérifier qu'aucune
      valeur sensible attendue n'est encore extractible.
- [x] **XLSX** : relire toutes les feuilles du classeur anonymisé final et
      scanner toutes les cellules de sortie.
- [x] **TXT** : garder un scanner final explicite sur le fichier texte généré,
      en plus du corpus moteur actuel.

#### P0.2 — Ajout manuel d'entités dans la preview

- [x] Permettre à l'utilisateur d'ajouter manuellement une entité ratée avant
      anonymisation finale : texte exact, label (`PER`, `ORG`, `ADDRESS`, etc.)
      et remplacement associé.
- [x] Couvrir les cas typiques : ajouter `Ambre`, une adresse complète, une
      société ou une référence sensible que le moteur n'a pas détectée.

#### P0.3 — Mode strict réel côté moteur

- [x] Ajouter un mode backend strict, distinct du simple profil GUI, qui active
      des heuristiques plus agressives : prénoms français dans une phrase,
      adresses probables, téléphones variés, emails obfusqués, acronymes isolés
      et valeurs sensibles dans des lignes contextualisées (`Nom:`, `Adresse:`,
      `Tel:`, `Email:`, `Dossier:`, etc.).
- [x] Propager `strictMode` via `config_options` API + GUI : le profil
      `Strict RGPD` active maintenant le vrai mode moteur.
- [x] Documenter clairement le compromis : en mode strict, un faux positif est
      accepté plus facilement qu'une fuite.

#### P0.4 — Détection de valeurs suspectes non anonymisées

- [x] Après anonymisation, scanner la sortie et remonter un avertissement du type
      : `Il reste peut-être 2 emails / 1 téléphone / 3 mots capitalisés suspects`.
      Le scanner ignore les placeholders et les valeurs de remplacement générées
      pour éviter les faux positifs sur les faux noms/adresses.
- [x] Exposer ces avertissements dans le résultat API (`privacy_warnings`,
      `privacy_warnings_count`) et dans la GUI sans bloquer le téléchargement.

#### P0.5 — Meilleure validation téléphone / IBAN

- [ ] Remplacer ou compléter la regex téléphone avec `phonenumbers` pour couvrir
      les numéros internationaux et réduire les faux positifs.
- [ ] Ajouter `python-stdnum` pour valider IBAN, SIRET/SIREN et autres identifiants
      français/européens pertinents.

#### P0.6 — Corpus qualité beaucoup plus gros

- [ ] Passer le corpus qualité à 50-100 cas réalistes : RH, contrats, emails,
      factures, logs, comptes rendus, documents juridiques et textes mal copiés
      depuis PDF/Word.
- [ ] Pour chaque cas, maintenir les valeurs sensibles attendues, les faux
      positifs à préserver et les labels attendus.

#### P0.7 — Score de confiance

- [ ] Calculer un score par anonymisation : nombre d'entités détectées, catégories
      couvertes, éléments suspects restants, volume de texte et niveau de risque.
- [ ] Afficher un niveau simple pour l'utilisateur : `faible`, `moyen`, `fort`,
      avec les raisons principales.

### Phase 9 — Prochaines améliorations produit / exploitation

- [ ] **Batch multi-fichiers complet** : finaliser le flux produit autour de
      plusieurs fichiers en une seule opération, avec statut par fichier,
      rapport global, erreurs isolées, export ZIP et possibilité de reprise.
- [ ] **Audit mobile complet** : vérifier tout le parcours sur téléphone
      (upload, preview, sélection d'entités, résultat, comparaison, mapping,
      désanonymisation, configuration) avec screenshots et contrôle
      d'absence de débordement horizontal.
- [ ] **Sécurité production** : confirmer que `ANONYFILES_API_KEY` est activée
      sur les déploiements publics, documenter la configuration côté GUI
      (`VITE_ANONYFILES_API_KEY`) et garder `/health` / docs accessibles sans
      exposer les endpoints de traitement.
- [ ] **Maintenance CI GitHub Actions** : nettoyer les warnings Node.js des
      actions (`actions/checkout`, `actions/setup-node`, `actions/setup-python`)
      quand les versions amont compatibles sont disponibles ; ce n'est pas un
      blocage tant que les jobs restent verts.
- [ ] **Typage Python progressif** : étendre `mypy` au moteur d'anonymisation
      au-delà de la cible actuelle pour attraper plus tôt les erreurs de type
      dans les chemins NER/remplacement/jobs.
- [ ] **Ménage GitHub** : fermer ou retraiter la PR historique
      [#72](https://github.com/simongrossi/anonyfiles/pull/72), qui semble
      obsolète ou partiellement absorbée par `main`.

---

## 4. Notes de vérification utiles

- Lancer les tests ciblés :
  `pytest tests/cli/test_docx_processor.py tests/cli/test_excel_processor.py tests/api/test_retention.py`
- Corpus qualité anonymisation :
  `uv run --python python3.11 --extra dev pytest -q tests/quality`
- Tests golden par format :
  `uv run --python python3.11 --extra dev pytest -q tests/golden`
- Diagnostic spaCy :
  `anonyfiles-cli utils spacy-status --model fr_core_news_md`
- Typage progressif core :
  `uv run --python python3.11 --extra dev mypy`
- Tests GUI : `cd anonyfiles_gui && npm test` (Vitest).
- L'environnement de dev complet : `pip install -e .[dev]` puis
  `python -m spacy download fr_core_news_md`.
- Réf. issue d'origine : https://github.com/simongrossi/anonyfiles/issues/73
