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

Une clé optionnelle **`strict_mode`** (ou `strictMode`) active les heuristiques
agressives du moteur (voir plus bas).

### Exemple minimal

```yaml
spacy_model: fr_core_news_md

replacements:
  PER:
    type: codes
    options:
      prefix: NOM

exclude_entities:
  - LOC
```

### Labels d'entités reconnus

| Label | Source de détection |
|---|---|
| `PER`, `LOC`, `ORG`, `MISC` | spaCy (NER) |
| `EMAIL`, `PHONE`, `IBAN`, `ADDRESS` | regex prioritaires |
| `DATE` | regex (validée) |

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

Chaque entité (`PER`, `ORG`, `LOC`, `EMAIL`, etc.) peut utiliser une stratégie.
Quatre `type` sont reconnus : **`codes`** (défaut), **`redact`**, **`placeholder`**
et **`faker`**. Si le `type` est absent ou inconnu, le moteur retombe sur `codes`.

### 1. **codes** — codification séquentielle *(défaut)*

Génère un code unique et séquentiel par entité (ex. `{{NOM_001}}`), ce qui conserve
la distinction des entités dans le document.

```yaml
ORG:
  type: codes
  options:
    prefix: ENTREPRISE   # → {{ENTREPRISE_001}}
    padding: 3
```

> ⚠️ Le type s'écrit **`codes`** (pluriel). Si `prefix` est omis, un tag par défaut
> est utilisé selon le label (`PER`→`NOM`, `ORG`→`ENTREPRISE`, `ADDRESS`→`ADRESSE`…).

---

### 2. **redact** — masquage statique

Remplace par un texte fixe, rendu unique par un index (ex. `[EMAIL_MASQUÉ]` →
`[EMAIL_MASQUÉ_1]`). Un `{}` dans `text` reçoit l'index.

```yaml
EMAIL:
  type: redact
  options:
    text: "[EMAIL_MASQUÉ]"
```

---

### 3. **placeholder** — format dynamique

Conserve le format en indiquant le type. Un `{}` dans `format` est remplacé par le
**texte original** de l'entité.

```yaml
DATE:
  type: placeholder
  options:
    format: "<DATE>"
```

---

### 4. **faker** — données réalistes

Génère des données plausibles (noms, villes, entreprises…). Le fournisseur est
choisi automatiquement selon le label (`PER`→nom, `LOC`→ville, `ORG`→société,
`EMAIL`, `PHONE`, `DATE`, `IBAN`). Options : `locale` et `consistent` (remplace
toujours une même valeur par le même faux).

```yaml
PER:
  type: faker
  options:
    locale: fr_FR
    consistent: true
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

## 🔒 Mode strict (`strict_mode`)

Activé via `strict_mode: true` (ou `strictMode`) — la GUI/API le propage par
`config_options` (profil **Strict RGPD**). Le moteur ajoute alors des heuristiques
plus agressives : prénoms français isolés, adresses probables, téléphones variés,
emails obfusqués (`nom [at] domaine [point] fr`), acronymes/lignes en majuscules et
valeurs sensibles dans des lignes contextualisées (`Nom:`, `Adresse:`, `Tel:`,
`Email:`, `Dossier:`…).

> Compromis assumé : en mode strict, un faux positif est accepté plus facilement
> qu'une fuite. Indépendamment de ce réglage, un scanner anti-fuite re-analyse la
> sortie finale et remonte des `privacy_warnings` (voir
> [`anonyfiles_api/README.md`](anonyfiles_api/README.md)).

---

## 📋 Exemple Complet (`config_default.yaml`)

Le fichier livré par défaut utilise la stratégie `codes` pour toutes les entités :

```yaml
spacy_model: fr_core_news_md

replacements:
  PER:
    type: codes
    options:
      prefix: NOM
      padding: 3

  LOC:
    type: codes
    options:
      prefix: FAKER_ADDRESS
      padding: 3

  ORG:
    type: codes
    options:
      prefix: ENTREPRISE_ANONYME
      padding: 3

  DATE:
    type: codes
    options:
      prefix: DATE_ANONYME
      padding: 3

  EMAIL:
    type: codes
    options:
      prefix: EMAIL
      padding: 3

  PHONE:
    type: codes
    options:
      prefix: TEL
      padding: 3

  IBAN:
    type: codes
    options:
      prefix: IBAN
      padding: 3

  ADDRESS:
    type: codes
    options:
      prefix: ADRESSE
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

