# 🧪 Tests

Ce dossier contient l'ensemble des tests automatisés du projet **Anonyfiles**, exécutés via [pytest](https://docs.pytest.org/).

## 📂 Structure

- **`unit/`** : Tests unitaires vérifiant le comportement isolé des composants (ex: anonymiser une chaine, charger une config).
- **`api/`** : Tests d'intégration pour l'API (FastAPI).
- **`cli/`** : Tests pour l'interface en ligne de commande (CLI).
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
pytest tests/quality
```

Le corpus qualité est piloté par `tests/quality/corpus/anonymization_cases.json`.
Il utilise le moteur réel avec des remplacements déterministes pour mesurer les
régressions sur noms, emails, téléphones, IBAN, dates, adresses, organisations
et faux positifs stables.
