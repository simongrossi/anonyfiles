# anonyfiles_cli/anonymizer/engine.py

import csv
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import typer

from .spacy_engine import SpaCyEngine
from .replacer import ReplacementSession
from .utils import apply_positional_replacements
from .audit import AuditLogger

# Import des nouveaux modules
from .custom_rules_processor import CustomRulesProcessor
from .ner_processor import NERProcessor
from .file_processor_factory import FileProcessorFactory
from .replacement_generator import ReplacementGenerator
from .writer import AnonymizedFileWriter


class AnonyfilesEngine:
    """
    Orchestre le processus complet d'anonymisation d'un fichier.
    """
    def __init__(self, config: Dict[str, Any],
                 exclude_entities_cli: Optional[List[str]] = None,
                 custom_replacement_rules: Optional[List[Dict[str, str]]] = None):
        
        self.config = config or {}
        
        # Initialisation du logger d'audit
        self.audit_logger = AuditLogger()

        # Initialisation du CustomRulesProcessor
        self.custom_rules_processor = CustomRulesProcessor(custom_replacement_rules, self.audit_logger)

        # Initialisation des entités à exclure
        self.entities_exclude = set()
        self.entities_exclude.update(self.config.get("exclude_entities", []))

        # Mapping des clés GUI aux labels spaCy et gestion des enabled_labels
        mapping_gui_keys = {
            "anonymizePersons": "PER", "anonymizeLocations": "LOC",
            "anonymizeOrgs": "ORG", "anonymizeEmails": "EMAIL",
            "anonymizeDates": "DATE", "anonymizeMisc": "MISC",
            "anonymizePhones": "PHONE", "anonymizeIbans": "IBAN",
            "anonymizeAddresses": "ADDRESS"
        }
        self.enabled_labels = set()
        for key, label in mapping_gui_keys.items():
            if self.config.get(key, True):
                self.enabled_labels.add(label)
            else:
                self.entities_exclude.add(label)

        if exclude_entities_cli:
            for e_list in exclude_entities_cli:
                 for e in e_list.split(","):
                    self.entities_exclude.add(e.strip().upper())

        # Initialisation de SpaCyEngine et NERProcessor
        model = self.config.get("spacy_model", "fr_core_news_md")
        self.spacy_engine = SpaCyEngine(model=model)
        self.ner_processor = NERProcessor(self.spacy_engine, self.enabled_labels, self.entities_exclude)
        
        # Initialisation du ReplacementGenerator
        self.replacement_generator = ReplacementGenerator(self.config, self.audit_logger)

        # Initialisation du Writer (dépend de dry_run, sera initialisé dans anonymize())
        self.writer: Optional[AnonymizedFileWriter] = None

        typer.echo(f"DEBUG (AnonyfilesEngine Init): Entités à exclure (config + CLI) : {self.entities_exclude}")


    def anonymize(self, input_path: Path, output_path: Optional[Path],
                  entities: Optional[List[str]], # Ce paramètre n'est plus utilisé directement ici, la logique de filtrage est dans NERProcessor
                  dry_run: bool,
                  log_entities_path: Optional[Path],
                  mapping_output_path: Optional[Path],
                  **kwargs) -> Dict[str, Any]:

        self.audit_logger.reset()
        self.custom_rules_processor.reset()
        self.writer = AnonymizedFileWriter(dry_run) # Initialise le writer pour cette exécution

        ext = input_path.suffix.lower()
        
        try:
            processor = FileProcessorFactory.get_processor(ext)
        except ValueError as e:
            return {"status": "error", "error": str(e), "audit_log": self.audit_logger.summary(), "total_replacements": self.audit_logger.total()}

        typer.echo(f"DEBUG (Engine): Type de processor choisi : {type(processor).__name__} pour extension {ext}")

        extract_kwargs = {}
        if hasattr(processor, 'has_header') and 'has_header' in kwargs: # Pour CsvProcessor
            extract_kwargs['has_header'] = kwargs['has_header']
        original_blocks = processor.extract_blocks(input_path, **extract_kwargs)

        # 1. Application des règles personnalisées
        blocks_after_custom_rules = []
        if self.custom_rules_processor.custom_rules:
            typer.echo(f"DEBUG (Engine): Application des règles personnalisées sur {len(original_blocks)} bloc(s) pour processeur {type(processor).__name__}.")
            for block_text in original_blocks:
                mod_block = self.custom_rules_processor.apply_to_block(block_text)
                blocks_after_custom_rules.append(mod_block)
            if self.custom_rules_processor.get_custom_replacements_count() > 0:
                 typer.echo(f"DEBUG (Engine): Nombre total de remplacements personnalisés effectués : {self.custom_rules_processor.get_custom_replacements_count()}")
        else:
            blocks_after_custom_rules = original_blocks
        
        # Vérification si le contenu est vide après règles custom
        if not any(block.strip() for block in blocks_after_custom_rules):
            typer.echo("INFO (Engine): Contenu vide après application des règles personnalisées (ou initialement vide).")
            if not dry_run and output_path:
                self.writer.write_anonymized_file(processor, output_path, [], input_path, **kwargs)
            if mapping_output_path and not dry_run:
                self.writer.write_mapping_file(mapping_output_path, self.custom_rules_processor.get_custom_replacements_mapping(), {}, [])
            return {
                "status": "success", "message": "Input effectively empty, no spaCy processing.",
                "entities_detected": [], "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        # 2. Détection des entités spaCy et regex
        unique_spacy_entities, spacy_entities_per_block_with_offsets = self.ner_processor.detect_entities_in_blocks(blocks_after_custom_rules)
        typer.echo(f"DEBUG (Engine): Entités spaCy uniques (après détection et filtres) à traiter : {len(unique_spacy_entities)}")

        # 3. Génération des remplacements spaCy et journalisation
        if not unique_spacy_entities and self.custom_rules_processor.get_custom_replacements_count() == 0:
            typer.echo("INFO (Engine): Aucune entité spaCy à anonymiser et aucune règle personnalisée n'a été appliquée.")
            if not dry_run and output_path:
                self.writer.write_anonymized_file(processor, output_path, blocks_after_custom_rules, input_path, **kwargs)
            if mapping_output_path and not dry_run:
                self.writer.write_mapping_file(mapping_output_path, self.custom_rules_processor.get_custom_replacements_mapping(), {}, [])
            return {
                "status": "success", "message": "No spaCy entities found to anonymize and no custom rules applied.",
                "entities_detected": [], "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        replacements_map_spacy, mapping_dict_spacy = self.replacement_generator.generate_spacy_replacements(
            unique_spacy_entities, spacy_entities_per_block_with_offsets
        )

        # 4. Application des remplacements spaCy positionnels
        truly_final_blocks_for_processor: List[str] = []
        for i, block_text_after_custom in enumerate(blocks_after_custom_rules):
            entities_in_this_block_to_replace = spacy_entities_per_block_with_offsets[i]
            
            # Filtrer les entités pour s'assurer qu'elles sont dans unique_spacy_entities (par le texte et le label)
            # Normalement, cela devrait déjà être le cas avec le NERProcessor, mais sécurité.
            unique_spacy_entities_set_of_tuples = set(unique_spacy_entities) # Pour recherche rapide
            filtered_entities_for_replacement_in_block = [
                ent_offset for ent_offset in entities_in_this_block_to_replace
                if (ent_offset[0], ent_offset[1]) in unique_spacy_entities_set_of_tuples
            ]

            if block_text_after_custom.strip() and filtered_entities_for_replacement_in_block:
                fully_anonymized_block = apply_positional_replacements(
                    block_text_after_custom,
                    replacements_map_spacy,
                    filtered_entities_for_replacement_in_block
                )
                truly_final_blocks_for_processor.append(fully_anonymized_block)
            else:
                truly_final_blocks_for_processor.append(block_text_after_custom)

        # 5. Écriture des fichiers de sortie
        if not dry_run:
            self.writer.write_anonymized_file(
                processor=processor,
                output_path=output_path,
                final_processed_blocks=truly_final_blocks_for_processor,
                original_input_path=input_path, 
                spacy_entities_per_block_with_offsets=spacy_entities_per_block_with_offsets, # Nécessaire pour PDF/DOCX
                **kwargs # Passe les kwargs restants (ex: has_header pour CSV/XLSX)
            )

            if log_entities_path:
                self.writer.write_log_entities_file(log_entities_path, unique_spacy_entities)

            if mapping_output_path:
                self.writer.write_mapping_file(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    mapping_dict_spacy,
                    unique_spacy_entities
                )

        total_replacements_logged = self.audit_logger.total()
        typer.echo(f"INFO (Engine): Anonymisation terminée. Total des remplacements (custom + spaCy) enregistrés dans l'audit : {total_replacements_logged}")

        return {
            "status": "success",
            "entities_detected": unique_spacy_entities,
            "output_path": str(output_path) if output_path and not dry_run else None,
            "replacements_applied_spacy": replacements_map_spacy,
            "audit_log": self.audit_logger.summary(),
            "total_replacements": total_replacements_logged,
        }