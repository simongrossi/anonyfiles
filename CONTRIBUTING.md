# CONTRIBUTING.md

Merci de votre intérêt pour contribuer à Anonyfiles !

## Comment proposer une contribution ?
1. Forkez ce dépôt et clonez-le en local.
2. Créez une nouvelle branche pour votre feature ou correction.
3. Créez un environnement Python 3.11+ puis installez le projet avec les
   outils de développement :

   ```bash
   python -m pip install -e ".[dev]"
   python -m spacy download fr_core_news_md
   ```

   puis assurez-vous que le code passe les tests (`pytest` pour Python, `npm run build` pour le front…).
   Un workflow GitHub Actions exécutera automatiquement `pytest` sur votre Pull Request.
4. Soumettez une Pull Request en expliquant clairement votre contribution.

## Règles de style
- Utilisez Black pour formater le code Python.
- Suivez la structure de fichiers du projet.

### Format des docstrings (style Google)
Nous utilisons le **style Google** pour toutes les docstrings. Ce format facilite
la génération automatique de la documentation et assure une présentation
cohérente dans l'ensemble du projet. Voici un exemple minimal :

```python
def saluer(nom: str) -> str:
    """Retourne un message de salutation.

    Args:
        nom: Nom de la personne à saluer.

    Returns:
        str: Le message final.
    """
    return f"Bonjour {nom}!"
```

## Tests
- Toute nouvelle fonctionnalité doit inclure un ou plusieurs tests unitaires.
- Les tests sont lancés automatiquement via GitHub Actions (workflow `ci.yml`).

### Lancer les tests localement

1. Installez le projet avec les dépendances de développement :

   ```bash
   python -m pip install -e ".[dev]"
   python -m spacy download fr_core_news_md
   ```

2. Exécutez la suite de tests :

   ```bash
   pytest
   ```

   Les composants graphiques (`anonyfiles_gui`) ne sont pas concernés et peuvent être ignorés pendant ces tests.

### Générer des données de test (Logs)

Pour tester l'interface de logs (TUI) ou le parsing, un script de génération est disponible :

```bash
# Génère 1000 logs au format standard
python scripts/generate_test_logs.py -n 1000

# Génère des logs au format Apache en continu (CTRL+C pour arrêter)
python scripts/generate_test_logs.py --live --format apache
```

## Gestion des dépendances

Le projet utilise une approche hybride moderne :

*   **`pyproject.toml`** : source de vérité unique. Il déclare Python 3.11+ et les dépendances abstraites avec des plages de versions (ex. `spacy>=3.8,<3.9`). C'est ce fichier qui est utilisé lors d'un `pip install .` ou `pip install -e ".[dev]"`.
*   **`requirements.txt`** : lock runtime généré automatiquement via `pip-tools`. Il contient les versions exactes utilisées par les déploiements reproductibles. Ne le modifiez pas à la main.

### Mettre à jour les dépendances

1.  Modifiez `pyproject.toml` pour ajouter/modifier une bibliothèque.
2.  Régénérez le `requirements.txt` :
    ```bash
    python -m piptools compile pyproject.toml -o requirements.txt
    ```

## Signaler un bug
Ouvrez un ticket GitHub avec un titre explicite et un maximum de détails !
