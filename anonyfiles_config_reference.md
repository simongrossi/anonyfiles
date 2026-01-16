# 🧩 Configuration (`config.yaml`)

Le fichier de configuration YAML est le cœur de la personnalisation d'Anonyfiles. 
Il permet de définir comment chaque type de données (noms, lieux, emails, etc.) doit être traité.

Par défaut, Anonyfiles cherche ce fichier dans :

```
~/.anonyfiles/config.yaml
```

Mais vous pouvez spécifier un autre fichier via :

```
anonyfiles-cli anonymize fichier.txt --config mon_fichier.yaml
```

---

## 🏗️ Structure Globale

Un fichier de configuration valide comporte trois sections principales :

1. **`spacy_model`** — modèle NLP utilisé
2. **`replacements`** — stratégie par type d'entité
3. **`exclude_entities`** — entités à ignorer

### Exemple minimal

```yaml
spacy_model: fr_core_news_md

replacements:
  PER:
    type: faker
    options:
      locale: fr_FR

exclude_entities:
  - LOC
```

---

## 🧠 Modèle NLP (`spacy_model`)

Permet de choisir le modèle spaCy pour la reconnaissance des entités :

| Modèle | Usage |
|---|---|
| `fr_core_news_md` | **Défaut** — bon compromis |
| `fr_core_news_lg` | Plus précis mais plus lourd |
| `fr_core_news_sm` | Rapide mais moins précis |

> Le modèle doit être installé avant usage :
>
> ```bash
> python -m spacy download fr_core_news_md
> ```

---

## 🛠️ Stratégies de Remplacement (`replacements`)

Chaque entité (`PER`, `ORG`, `LOC`, `EMAIL`, etc.) peut utiliser une stratégie :

### 1. **faker** — données réalistes

Génère des données plausibles (noms, adresses, entreprises).

```yaml
PER:
  type: faker
  options:
    locale: fr_FR
```

---

### 2. **code** — codification séquentielle

Conserve la distinction des entités dans le document.

```yaml
ORG:
  type: code
  options:
    prefix: ENTREPRISE_
    padding: 3    # → ENTREPRISE_001
```

---

### 3. **redact** — masquage statique

Remplace par un texte fixe.

```yaml
EMAIL:
  type: redact
  options:
    text: "[EMAIL_MASQUÉ]"
```

---

### 4. **placeholder** — format dynamique

Permet de conserver le format tout en indiquant le type.

```yaml
DATE:
  type: placeholder
  options:
    format: "<DATE:{}>"
```

---

## 🚫 Exclusion (`exclude_entities`)

Les entités listées ici seront laissées intactes.

```yaml
exclude_entities:
  - LOC  # villes, pays non modifiés
  - MISC
```

---

## 📋 Exemple Complet (`config_default.yaml`)

```yaml
spacy_model: fr_core_news_md

replacements:
  # Personnes → faux noms FR
  PER:
    type: faker
    options:
      locale: fr_FR

  # Entreprises → codes
  ORG:
    type: code
    options:
      prefix: ORG_
      padding: 3

  # Lieux → fausses adresses
  LOC:
    type: faker
    options:
      locale: fr_FR
      provider: address

  # Dates → masque simple
  DATE:
    type: redact
    options:
      text: "[DATE]"

  # Emails → codes
  EMAIL:
    type: code
    options:
      prefix: MAIL_
      padding: 3

exclude_entities:
  - MISC
```

---

## ✅ Validation de la Configuration

Avant un traitement important, validez votre fichier avec :

```bash
anonyfiles-cli config validate-config mon_fichier.yaml
```

Cela permet d'éviter les erreurs de schéma ou d'options.

