🖥️ Anonyfiles CLIAnonyfiles CLI est l’outil en ligne de commande du projet Anonyfiles, conçu pour anonymiser et désanonymiser des documents texte, tableurs et fichiers bureautiques.Il s’appuie sur le NLP (spaCy), une configuration flexible en YAML, et des règles personnalisables pour garantir la confidentialité des données sensibles.🚀 Fonctionnalités principalesMulti-format :.txt, .csv, .docx, .xlsx, .pdf, .jsonPrise en charge des fichiers vides et volumineuxDétection automatique d’entités avec spaCy :Personnes (PER), Lieux (LOC), Organisations (ORG), Dates, Emails, Téléphones, IBAN, Adresses...Configuration YAML flexible :Stratégies d’anonymisation par type d’entité : faker, code, masquage, placeholder...Activation/désactivation de certains types d’entitésSupport d'une configuration utilisateur par défaut (~/.anonyfiles/config.yaml)Règles personnalisées supplémentaires :Règles simples de remplacement (texte ou regex) injectables en ligne de commande, avant le NLPExport de mapping détaillé :CSV listant chaque entité remplacée automatiquement via spaCyFichiers de logs CSV pour auditMode batch :Traitement d’un dossier complet de fichiers (Fonctionnalité ✅ Réalisée)Désanonymisation réversible :Restauration des fichiers à partir du mappingRobustesse et performance :Chargement paresseux de spaCy, gestion fine des erreurs, cache en mémoireInterface console enrichie (Rich)🛠️ Prérequis & Installation🛆 Dépendances techniquesPython 3.9+ (version testée et recommandée pour la CLI)pip et environnements virtuels recommandésModèle spaCy fr_core_news_md ou lg🧪 Installation rapidegit clone https://github.com/simongrossi/anonyfiles.git
cd anonyfiles/anonyfiles_cli
pip install -r requirements.txt
python -m spacy download fr_core_news_md
📁 Structure du projet refactoriséeLe projet anonyfiles_cli est conçu de manière modulaire, avec une séparation claire des responsabilités.À la racine :main.py : point d’entrée simplifié pour python -m anonyfiles_cli.mainrequirements.txt : dépendances PythonREADME.md : documentationexceptions.py : Définition des classes d'exceptions personnalisées.anonymizer/anonyfiles_core.py : coordination du processus principalspacy_engine.py : instanciation spaCy et regexreplacer.py : remplacements d’entités selon config YAML*_processor.py : traitements spécifiques par type de fichieraudit.py : export CSV des entitésutils.py : outils diversdeanonymize.py : lecture du mapping CSV pour restaurermanagers/config_manager.py : fusion config utilisateur / CLI / YAMLpath_manager.py : gestion des chemins de sortie, mapping, logsvalidation_manager.py : validation YAML (Cerberus)ui/console_display.py : affichage console enrichi (Rich)interactive_mode.py : préparation d'un mode CLI interactifconfig/config.yaml : exemple de config utilisateurgenerated_config.yaml : généré par interface ou APIschema.yaml : schéma de validation YAMLcommands/Contient les modules pour chaque commande CLI (e.g., anonymize.py, deanonymize.py, config.py, batch.py, utils.py), simplifiant le main.py.handlers/Contient la logique métier des commandes (e.g., anonymize_handler.py, batch_handler.py, validation_handler.py).utils/Contient les utilitaires partagés (e.g., system_utils.py).Sorties & tests :output_files/ : fichiers anonymiséslog/ : logs CSVmappings/ : fichiers de correspondanceexamples/ : jeux de donnéestests/ : tests unitaires à compléter💡 Utilisation rapide▶️ Exemple simple (Anonymisation)python3 -m anonyfiles_cli.main anonymize process anonyfiles_cli/input.txt
▶️ Exemple avancé (Anonymisation)python3 -m anonyfiles_cli.main anonymize process anonyfiles_cli/input.txt \
  --output-dir anonyfiles_cli/output_test \
  --config anonyfiles_cli/config/config.yaml \
  --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]' \
  --log-entities anonyfiles_cli/log/log.csv \
  --mapping-output anonyfiles_cli/mappings/mapping.csv
📌 Options CLI résuméesOptionDescriptionINPUT_FILEFichier à anonymiser--configFichier YAML de configuration--custom-replacements-jsonRemplacements simples JSON--output / -oFichier de sortie--output-dirDossier de sortie--forceÉcrase les fichiers--exclude-entitiesEntités spaCy à exclure--log-entitiesExport CSV d’audit--mapping-outputFichier CSV de mapping--has-header-opttrue ou false pour CSV--csv-no-headerCSV sans en-tête--append-timestampAjoute un horodatage--dry-runMode simulation✨ Règles personnalisées (avant spaCy)python3 -m anonyfiles_cli.main anonymize process fichier.txt \
  --config config.yaml \
  --custom-replacements-json '[{"pattern": "ProjetX", "replacement": "[SECRET_PROJET]", "isRegex": false}]'
⚠️ Ces remplacements ne sont pas inclus dans le mapping CSV.🔄 Désanonymisationpython3 -m anonyfiles_cli.main deanonymize process fichier_anonymise.txt \
  --mapping-csv anonyfiles_cli/mappings/mapping.csv \
  -o anonyfiles_cli/fichier_restaure.txt \
  --permissive
🧹 Exemple de fichier config.yamlspacy_model: fr_core_news_md
replacements:
  PER:
    type: faker
    options:
      locale: fr_FR
  ORG:
    type: code
    options:
      prefix: ORG_
      padding: 4
  EMAIL:
    type: redact
    options:
      text: "[EMAIL_CONFIDENTIEL]"
  DATE:
    type: placeholder
    options:
      format: "[DATE:{}]"
exclude_entities:
  - ORG
🔍 Entités supportées & stratégies YAMLEntitéLabelExempleStratégies disponiblesPersonnePERJean Dupontfaker, code, redact, placeholderOrganisationORGACME Corp.faker, code, redact, placeholderLieuLOCParis, Nantesfaker, code, redact, placeholderEmailEMAILcontact@domaine.comfaker, code, redact, placeholderDateDATE12/05/2023faker, code, redact, placeholderTéléphonePHONE0612345678faker, code, redact, placeholderIBANIBANFR7612345678901234567890faker, code, redact, placeholderAdresseADDRESS10 rue Victor Hugofaker, code, redact, placeholder📌 Essayez fr_core_news_lg si certaines entités sont mal détectées.🗌 Conseils d’usage & limites✅ ConseilsTester avec des données non sensiblesOrganiser les répertoires : input_files, output_files, log, mappingsBien définir ses regex personnaliséesLancer depuis la racine avec python3 -m anonyfiles_cli.main⚠️ Limites actuellesPDF et DOCX peu testés (TXT, CSV, JSON OK)--custom-replacements-json non inclus dans le mapping CSVDésanonymisation uniquement sur entités NLPCertaines entités nécessitent fr_core_news_lgPas encore de nettoyage auto des fichiers temporaires🔭 Roadmap / En coursAudit des remplacements manuelsGénération interactive d’un config.yamlValidateur de règles personnaliséesMode batch avec parallélisation (✅ Réalisé)Barre de progressionMode interactif CLI (choix entités)📜 LicenceDistribué sous licence MIT.📚 Liens utiles📦 Projet complet GitHub🖼️ Interface graphique Anonyfiles GUI📖 spaCy Docs🎲 Faker Docs💎 Rich Docs