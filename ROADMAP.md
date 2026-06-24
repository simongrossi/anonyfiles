# Roadmap & audit technique — Anonyfiles

> Document de suivi créé le **2026-06-25**. Objectif : centraliser l'audit
> (documentation + dépendances) et le plan d'action priorisé, pour pouvoir
> reprendre le travail plus tard. Cocher les cases au fur et à mesure.

---

## 0. Contexte / travail déjà réalisé

Branches en cours (non mergées, **rien n'est encore poussé**) :

| Branche | Contenu | État |
|---|---|---|
| `fix/docx-upload-and-anonymization` | Fix issue #73 (le champ `file` n'était jamais envoyé pour docx/pdf/json → 422) + durcissement docx (en-têtes/pieds de page anonymisés, `ValueError` sur mismatch, fichier corrompu) + même fix mismatch côté Excel + tests GUI Vitest + docs | ✅ 3 commits |
| `feat/job-retention` | Empilée sur la précédente : purge automatique des jobs expirés (TTL configurable, env `ANONYFILES_JOB_RETENTION_HOURS`) — confidentialité | ✅ 4 commits (superset) |

> `feat/job-retention` contient **tout** (c'est un sur-ensemble de la branche fix).

À faire côté Git : décider de la stratégie de merge / PR et **pousser**.

---

## 1. Audit documentation (`.md`)

**Problème central : trois récits contradictoires sur la gestion des dépendances**,
et des fichiers référencés qui n'existent pas.

- [ ] **🔴 `CONTRIBUTING.md` (l.11, 49, 76-84)** : référence `pip install -r requirements-test.txt`
  et `pip-compile pyproject.toml -o requirements.txt` — ces `.txt` **n'existent pas**.
- [ ] **🔴 `deploy/README.md` (l.7)** : prétend que le Dockerfile installe `requirements-full.txt`
  (faux : il fait `pip install .`) et ce fichier est **manquant**.
- [ ] **🔴 `nixpacks.toml`** : `pip install -r requirements-full.txt` → fichier absent →
  **déploiement Railway/nixpacks cassé**.
- [ ] **🟠 `anonyfiles_core/README.md` (l.17)** : « Chaque module possède son `requirements.txt` »
  → contredit la centralisation `pyproject.toml`.
- [ ] **🟠 `anonyfiles_cli/README.anonyfiles_cli.md` (l.48)** : `pip install -r requirements.txt`
  alors que ce fichier est un stub « obsolète ».
- [ ] **🟠 `anonyfiles_gui/README.anonyfiles_gui.md` (l.26)** : exige **Python 3.9+** alors que
  tout le reste (et `pyproject`) exige **3.11+**.
- [ ] **🟠 `README.md` (l.439) + `CHANGELOG.md`** : « Plus de `requirements.txt` ! » contredit
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
- [ ] Bumper les **modèles spaCy → 3.8.0** + `spacy>=3.8,<3.9`, lever le plafond numpy
      (`>=1.26` autorise 2.x), pandas `>=2.2`.
- [ ] **Une seule source de vérité** : garder `pyproject.toml`, supprimer/aligner
      `requirements.in`, `requirements-test.in`, `anonyfiles_api/requirements.txt`
      (retirer les pins `fastapi==0.111`, `spacy==3.7.5`).
- [ ] Régénérer **et commiter** un lock unique (`pip-compile pyproject.toml`) **ou** assumer
      100 % pyproject. Créer le `requirements-full.txt` manquant **ou** corriger
      `nixpacks.toml` en `pip install .` (déploiement actuellement cassé).
- [ ] Valider : `pip install .` + `python -m spacy download fr_core_news_md` + suite de tests
      verte **sous numpy 2**.

### Phase 1 — Cohérence doc (rapide, juste après Phase 0)
- [ ] Corriger CONTRIBUTING / `deploy/README` / `core/README` / cli README / gui README
      (Python 3.11, vraie stratégie de déps). Tout doit raconter **la même** histoire.

### Phase 2 — Dette technique ciblée
- [ ] Pydantic v2 : `class Config` → `ConfigDict` (supprime les warnings).
- [ ] Supprimer les méthodes `replace_entities` legacy restantes (pdf/excel/json) — mortes.
- [ ] Corriger la ligne dupliquée `anonyfiles_api/routers/anonymization.py:132`.
- [ ] Retirer les fichiers parasites versionnés : `debug_job_mock.py`, `input.txt`,
      `input_test.txt`, `validate_fix_final.py`.

### Phase 3 — Modernisation front (chantiers séparés, un par un)
- [ ] Vite 4 → 6/7.
- [ ] Svelte 4 → 5 (migration runes).
- [ ] Tailwind 3 → 4.

### Phase 4 — Sécurité / robustesse
- [ ] Merger les branches en cours (`fix/docx…`, `feat/job-retention`) + pousser/PR.
- [ ] Auth optionnelle sur l'API (clé API activable par config) pour les déploiements publics.

---

## 4. Notes de vérification utiles

- Lancer les tests ciblés :
  `pytest tests/cli/test_docx_processor.py tests/cli/test_excel_processor.py tests/api/test_retention.py`
- Tests GUI : `cd anonyfiles_gui && npm test` (Vitest).
- L'environnement de dev complet : `pip install -e .[dev]` puis
  `python -m spacy download fr_core_news_md`.
- Réf. issue d'origine : https://github.com/simongrossi/anonyfiles/issues/73
