# Manuel de Référence CLI

L'outil **Anonyfiles CLI** (`anonyfiles-cli`) est l'interface en ligne de commande principale pour interagir avec le moteur d'anonymisation. Elle permet l'automatisation, le traitement par lots et l'intégration dans des scripts.

---

## 🚀 Commande : `anonymize`

Commande principale pour traiter un fichier et masquer les données sensibles.

### Usage

```bash
anonyfiles-cli anonymize [OPTIONS] INPUT_FILE
```

### Arguments

`INPUT_FILE` : Chemin vers le fichier à traiter (`.txt`, `.docx`, `.xlsx`, `.pdf`, `.json`, `.csv`).

### Options

| Option | Raccourci | Description |
|---|---|---|---|
| `--output-dir` |  | Dossier racine pour les sorties. Un sous-dossier (Job ID) y sera créé. |
| `--config` |  | Chemin vers un fichier de configuration YAML personnalisé. |
| `--custom-replacements-json` |  | Chaîne JSON ou fichier (`@file.json`) contenant des règles regex appliquées avant le moteur NLP. |
| `--interactive` | `-i` | Mode interactif pour sélectionner les types d'entités à masquer. |
| `--exclude-entities` |  | Liste de types d'entités à ignorer (ex : `LOC,DATE`). |
| `--mapping-output` |  | Chemin spécifique pour exporter le mapping CSV (original ↔ code). |
| `--log-entities` |  | Chemin spécifique pour le journal d'audit des entités trouvées. |
| `--force` |  | Écrase le fichier de sortie s'il existe déjà. |
| `--dry-run` |  | Simulation sans modification de fichiers. |
| `--csv-no-header` |  | Indique que le CSV d'entrée n'a pas d'en-tête. |

### Exemples

**1. Anonymisation simple**
```bash
anonyfiles-cli anonymize cv_candidat.docx
```

**2. Avec configuration et sortie spécifique**
```bash
anonyfiles-cli anonymize data.xlsx   --output-dir ./resultats   --config my_config.yaml
```

**3. Avec règles personnalisées (Regex)**
```bash
anonyfiles-cli anonymize rapport.txt   --custom-replacements-json '[{"pattern": "Projet-[A-Z0-9]+", "replacement": "[PROJET]", "isRegex": true}]'
```

---

## 🔄 Commande : `deanonymize`

Permet de restaurer un fichier original en utilisant le fichier de mapping.

### Usage

```bash
anonyfiles-cli deanonymize [OPTIONS] INPUT_FILE
```

### Options

| Option | Description |
|---|---|
| `--mapping-csv` | **Requis.** Fichier CSV des correspondances généré par `anonymize`. |
| `--output`, `-o` | Chemin du fichier restauré. |
| `--permissive` | Continue même si certains codes ne sont pas trouvés. |

### Exemple

```bash
anonyfiles-cli deanonymize document_anonymized.txt   --mapping-csv mapping.csv   -o document_original_restaure.txt
```

---

## 🧹 Commande : `job`

Gère les tâches d'anonymisation passées. Chaque exécution crée un dossier unique basé sur un timestamp.

### Usage

```bash
anonyfiles-cli job [COMMAND]
```

### Sous-commandes

#### `list`
Liste les jobs disponibles.

```bash
anonyfiles-cli job list
```

#### `delete`
Supprime un job et ses fichiers.

```bash
anonyfiles-cli job delete <JOB_ID>
```

Exemple :

```bash
anonyfiles-cli job delete 20231025-143022
```

Ajouter `--force` pour supprimer sans confirmation.

---

## 📊 Commande : `logs`

Outils pour consulter les journaux d'audit.

### Usage

```bash
anonyfiles-cli logs [COMMAND]
```

### Sous-commandes

#### `interactive`
Interface TUI temps réel.

```bash
anonyfiles-cli logs interactive
```

#### `list`
Affiche les fichiers de logs.

```bash
anonyfiles-cli logs list
```

#### `clear`
Supprime tous les logs.

```bash
anonyfiles-cli logs clear
```

---

## ⚙️ Commande : `config`

Utilitaires pour gérer la configuration YAML.

### `validate-config`

```bash
anonyfiles-cli config validate-config ma_config.yaml
```

---

## 💡 Règles Personnalisées (JSON)

`--custom-replacements-json` permet d'injecter des règles rapides.

### Format JSON

```json
[
  {
    "pattern": "Texte à trouver",
    "replacement": "Texte de remplacement",
    "isRegex": false
  },
  {
    "pattern": "\\d{4}-\\d{4}",
    "replacement": "[CODE_SERIE]",
    "isRegex": true
  }
]
```

### Astuce

Stockez ce JSON dans un fichier :

```bash
anonyfiles-cli anonymize fichier.txt --custom-replacements-json @regles.json
```
