# 🧪 Tests

Ce dossier contient l'ensemble des tests automatisés du projet **Anonyfiles**, exécutés via [pytest](https://docs.pytest.org/).

## 📂 Structure

- **`unit/`** : Tests unitaires vérifiant le comportement isolé des composants (ex: anonymiser une chaine, charger une config).
- **`api/`** : Tests d'intégration pour l'API (FastAPI).
- **`cli/`** : Tests pour l'interface en ligne de commande (CLI).
- **`golden/`** : Snapshots par format pour vérifier reconstruction, absence de fuite et lisibilité des sorties.
- **`quality/`** : Corpus qualité anonymisation avec données sensibles attendues, faux positifs à préserver et mapping vérifié.
- **`conftest.py`** : Configuration et fixtures partagées pour Pytest.

## 🚀 Exécution des tests

Pour lancer tous les tests depuis la racine du projet :

```bash
pytest
```

Pour lancer une catégorie spécifique :

```bash
pytest tests/unit
pytest tests/api
pytest tests/golden
pytest tests/quality
```

Le corpus qualité est piloté par `tests/quality/corpus/anonymization_cases.json`.
Il utilise le moteur réel avec des remplacements déterministes pour mesurer les
régressions sur noms, emails, téléphones, IBAN, dates, adresses, organisations
et faux positifs stables.

Les tests golden reconstruisent des fichiers TXT, CSV, DOCX, XLSX, PDF et JSON
depuis des entrées minimales générées en test, puis comparent une représentation
stable du fichier final au snapshot attendu.

## 🔎 Typage progressif

La cible `mypy` est volontairement progressive et configurée dans `pyproject.toml`.
Elle couvre les types partagés du core, les processors formats, la factory et le
writer :

```bash
uv run --python python3.11 --extra dev mypy
```
