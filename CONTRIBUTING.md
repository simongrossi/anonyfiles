# CONTRIBUTING.md

Merci de votre intérêt pour contribuer à Anonyfiles !

## Comment proposer une contribution ?
1. Forkez ce dépôt et clonez-le en local.
2. Créez une nouvelle branche pour votre feature ou correction.
3. Installez les dépendances de test :

   ```bash
   pip install -r requirements-test.txt
   ```

   puis assurez-vous que le code passe les tests (`pytest` pour Python, `npm run build` pour le front…).
   Un workflow GitHub Actions exécutera automatiquement `pytest` sur votre Pull Request.
4. Soumettez une Pull Request en expliquant clairement votre contribution.

## Règles de style
- Utilisez Black pour formater le code Python.
- Suivez la structure de fichiers du projet.

## Tests
- Toute nouvelle fonctionnalité doit inclure un ou plusieurs tests unitaires.
- Les tests sont lancés automatiquement via GitHub Actions (workflow `ci.yml`).

### Lancer les tests localement

1. Installez les dépendances de test :

   ```bash
   pip install -r requirements-test.txt
   ```

2. Exécutez la suite de tests :

   ```bash
   pytest
   ```

   Les composants graphiques (`anonyfiles_gui`) ne sont pas concernés et peuvent être ignorés pendant ces tests.

## Signaler un bug
Ouvrez un ticket GitHub avec un titre explicite et un maximum de détails !
