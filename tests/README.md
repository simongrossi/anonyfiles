# 🧪 Tests

Ce dossier contient l'ensemble des tests automatisés du projet **Anonyfiles**, exécutés via [pytest](https://docs.pytest.org/).

## 📂 Structure

- **`unit/`** : Tests unitaires vérifiant le comportement isolé des composants (ex: anonymiser une chaine, charger une config).
- **`api/`** : Tests d'intégration pour l'API (FastAPI).
- **`cli/`** : Tests pour l'interface en ligne de commande (CLI).
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
```
