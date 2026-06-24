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

> ⚠️ **À valider en CI** : `pandas 3.0` / `numpy 2.4` n'ont pas pu être testés en local
> (Python 3.9 ici, le projet exige 3.11). La CI (Python 3.11) est le filet de sécurité.

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
- [ ] Valider : `pip install .` + `python -m spacy download fr_core_news_md` + suite de tests
      verte **sous numpy 2**.

### Phase 1 — Cohérence doc (rapide, juste après Phase 0)
- [x] Corriger CONTRIBUTING / `deploy/README` / `core/README` / cli README / gui README
      (Python 3.11, vraie stratégie de déps). Tout doit raconter **la même** histoire.

### Phase 2 — Dette technique ciblée
- [ ] Pydantic v2 : `class Config` → `ConfigDict` (supprime les warnings).
- [x] Supprimer les méthodes `replace_entities` legacy restantes (pdf/excel/json) — mortes.
- [x] Corriger la ligne dupliquée `anonyfiles_api/routers/anonymization.py:132`.
- [x] Retirer les fichiers parasites versionnés : `debug_job_mock.py`, `input.txt`,
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
