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
- [ ] **(différé)** Nettoyer le smell de `spacy_engine.py` (`_active_spacy_module`, gardes
      `getattr/hasattr`). Tentative annulée (commit revert) : ces contournements assurent en
      fait une **résilience réelle** contre le stubbing de `spacy` via `sys.modules` dans
      plusieurs tests (`test_cli_e2e`, `test_job_cli`, `test_health`). Le faire proprement =
      retravailler ces stubs (les rendre complets / supprimer les stubs obsolètes maintenant
      que spaCy est une dépendance dure) **et** valider `test_full_flow` avec le vrai modèle
      sur le stack moderne — à faire en local avec Python 3.11 + modèle spaCy installé.
- [x] Supprimer les méthodes `replace_entities` legacy restantes (pdf/excel/json) — mortes.
- [x] Corriger la ligne dupliquée `anonyfiles_api/routers/anonymization.py:132`.
- [x] Retirer les fichiers parasites versionnés : `debug_job_mock.py`, `input.txt`,
      `input_test.txt`, `validate_fix_final.py`.

### Phase 3 — Modernisation front (chantiers séparés, un par un)
- [ ] Vite 4 → 6/7.
- [ ] Svelte 4 → 5 (migration runes).
- [ ] Tailwind 3 → 4.

### Phase 4 — Sécurité / robustesse
- [x] Merger les branches en cours (`fix/docx…`, `feat/job-retention`) + pousser/PR.
- [ ] Auth optionnelle sur l'API (clé API activable par config) pour les déploiements publics.

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
- [ ] **Typage progressif du core** : introduire `mypy` ou `pyright` progressivement sur
      `anonyfiles_core`, en priorité les processors, le moteur et les retours d'API internes.

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
- [ ] **Profils d'anonymisation** : proposer des presets (`strict RGPD`, `léger`,
      `documents RH`, `contrats`, `logs techniques`) au-dessus des options détaillées.
- [ ] **Prévisualisation des entités détectées** : afficher les entités avant traitement final,
      permettre de décocher/corriger, puis lancer l'anonymisation.
- [ ] **Batch complet** : traitement multi-fichiers avec rapport global, erreurs par fichier,
      ZIP final et reprise possible.

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
- Tests GUI : `cd anonyfiles_gui && npm test` (Vitest).
- L'environnement de dev complet : `pip install -e .[dev]` puis
  `python -m spacy download fr_core_news_md`.
- Réf. issue d'origine : https://github.com/simongrossi/anonyfiles/issues/73
