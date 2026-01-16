# anonyfiles_cli/anonymizer/engine.py

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .spacy_engine import SpaCyEngine
from .utils import apply_positional_replacements
from .audit import AuditLogger

# Import des nouveaux modules
from .custom_rules_processor import CustomRulesProcessor
from .ner_processor import NERProcessor
from .file_processor_factory import FileProcessorFactory
from .replacement_generator import ReplacementGenerator
from .writer import AnonymizedFileWriter

logger = logging.getLogger(__name__)


class AnonyfilesEngine:
    """
    Orchestre le processus complet d'anonymisation d'un fichier.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        exclude_entities_cli: Optional[List[str]] = None,
        custom_replacement_rules: Optional[List[Dict[str, str]]] = None,
    ):
        self.config = config or {}

        # Initialisation du logger d'audit
        self.audit_logger = AuditLogger()

        # Initialisation du CustomRulesProcessor
        self.custom_rules_processor = CustomRulesProcessor(
            custom_replacement_rules, self.audit_logger
        )

        # Initialisation des entités à exclure
        self.entities_exclude = set()
        self.entities_exclude.update(self.config.get("exclude_entities", []))

        # Mapping des clés GUI aux labels spaCy et gestion des enabled_labels
        mapping_gui_keys = {
            "anonymizePersons": "PER",
            "anonymizeLocations": "LOC",
            "anonymizeOrgs": "ORG",
            "anonymizeEmails": "EMAIL",
            "anonymizeDates": "DATE",
            "anonymizeMisc": "MISC",
            "anonymizePhones": "PHONE",
            "anonymizeIbans": "IBAN",
            "anonymizeAddresses": "ADDRESS",
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
        self.ner_processor = NERProcessor(
            self.spacy_engine, self.enabled_labels, self.entities_exclude
        )

        # Initialisation du ReplacementGenerator
        self.replacement_generator = ReplacementGenerator(
            self.config, self.audit_logger
        )

        # Initialisation du Writer (dépend de dry_run, sera initialisé dans anonymize())
        self.writer: Optional[AnonymizedFileWriter] = None

        logger.debug(
            "DEBUG (AnonyfilesEngine Init): Entités à exclure (config + CLI) : %s",
            self.entities_exclude,
        )

    def _process_content(self, original_blocks: List[str]):
        """
        Logique métier pure d'anonymisation sur des blocs de texte.
        Retourne un dictionnaire contenant les résultats intermédiaires ou finaux.
        """
        # 1. Application des règles personnalisées
        blocks_after_custom_rules = []
        if self.custom_rules_processor.custom_rules:
            logger.debug(
                "DEBUG (Engine): Application des règles personnalisées sur %s bloc(s).",
                len(original_blocks),
            )
            for block_text in original_blocks:
                mod_block = self.custom_rules_processor.apply_to_block(block_text)
                blocks_after_custom_rules.append(mod_block)
            if self.custom_rules_processor.get_custom_replacements_count() > 0:
                logger.debug(
                    "DEBUG (Engine): Nombre total de remplacements personnalisés : %s",
                    self.custom_rules_processor.get_custom_replacements_count(),
                )
        else:
            blocks_after_custom_rules = original_blocks

        # Vérification si le contenu est vide
        if not any(block.strip() for block in blocks_after_custom_rules):
            return {
                "decision": "empty",
                "blocks_after_custom": blocks_after_custom_rules,
            }

        # 2. Détection des entités spaCy et regex
        unique_spacy_entities, spacy_entities_per_block_with_offsets = (
            self.ner_processor.detect_entities_in_blocks(blocks_after_custom_rules)
        )
        logger.debug(
            "DEBUG (Engine): Entités spaCy uniques détectées : %s",
            len(unique_spacy_entities),
        )

        # Vérification si rien à faire
        if (
            not unique_spacy_entities
            and self.custom_rules_processor.get_custom_replacements_count() == 0
        ):
            return {
                "decision": "no_changes",
                "blocks_after_custom": blocks_after_custom_rules,
                "unique_spacy_entities": [],
            }

        # 3. Génération des remplacements
        replacements_map_spacy, mapping_dict_spacy = (
            self.replacement_generator.generate_spacy_replacements(
                unique_spacy_entities, spacy_entities_per_block_with_offsets
            )
        )

        # 4. Application des remplacements positionnels
        truly_final_blocks = []
        unique_spacy_entities_set = set(unique_spacy_entities)  # Opti lookup

        for i, block_text_after in enumerate(blocks_after_custom_rules):
            entities_in_block = spacy_entities_per_block_with_offsets[i]

            # Filtrage de sécurité
            filtered_entities = [
                ent
                for ent in entities_in_block
                if (ent[0], ent[1]) in unique_spacy_entities_set
            ]

            if block_text_after.strip() and filtered_entities:
                fully_anonymized = apply_positional_replacements(
                    block_text_after,
                    replacements_map_spacy,
                    filtered_entities,
                )
                truly_final_blocks.append(fully_anonymized)
            else:
                truly_final_blocks.append(block_text_after)

        return {
            "decision": "processed",
            "final_blocks": truly_final_blocks,
            "unique_spacy_entities": unique_spacy_entities,
            "spacy_entities_per_block": spacy_entities_per_block_with_offsets,
            "replacements_map_spacy": replacements_map_spacy,
            "mapping_dict_spacy": mapping_dict_spacy,
        }

    def anonymize(
        self,
        input_path: Path,
        output_path: Optional[Path],
        entities: Optional[
            List[str]
        ],  # Ce paramètre n'est plus utilisé directement ici, la logique de filtrage est dans NERProcessor
        dry_run: bool,
        log_entities_path: Optional[Path],
        mapping_output_path: Optional[Path],
        **kwargs,
    ) -> Dict[str, Any]:
        self.audit_logger.reset()
        self.custom_rules_processor.reset()
        self.writer = AnonymizedFileWriter(dry_run)

        ext = input_path.suffix.lower()
        try:
            processor = FileProcessorFactory.get_processor(ext)
        except ValueError as e:
            return self._error_response(e)

        logger.debug(
            f"DEBUG (Engine): Processing {input_path} with {type(processor).__name__}"
        )

        extract_kwargs = {}
        if hasattr(processor, "has_header") and "has_header" in kwargs:
            extract_kwargs["has_header"] = kwargs["has_header"]

        original_blocks = processor.extract_blocks(input_path, **extract_kwargs)

        # Appel Logique Métier
        result = self._process_content(original_blocks)
        decision = result["decision"]

        # Gestion des sorties selon la décision
        if decision == "empty":
            logger.info("INFO (Engine): Contenu vide.")
            if not dry_run and output_path:
                self.writer.write_anonymized_file(
                    processor, output_path, [], input_path, **kwargs
                )
            if mapping_output_path and not dry_run:
                self.writer.write_mapping_file(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    {},
                    [],
                )
            return self._success_response("Input empty", [])

        elif decision == "no_changes":
            logger.info("INFO (Engine): Aucune modification requise.")
            if not dry_run and output_path:
                self.writer.write_anonymized_file(
                    processor,
                    output_path,
                    result["blocks_after_custom"],
                    input_path,
                    **kwargs,
                )
            if mapping_output_path and not dry_run:
                self.writer.write_mapping_file(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    {},
                    [],
                )
            return self._success_response("No changes applied", [])

        # Cas nominal: processed
        if not dry_run:
            self.writer.write_anonymized_file(
                processor=processor,
                output_path=output_path,
                final_processed_blocks=result["final_blocks"],
                original_input_path=input_path,
                spacy_entities_per_block_with_offsets=result[
                    "spacy_entities_per_block"
                ],
                **kwargs,
            )
            if log_entities_path:
                self.writer.write_log_entities_file(
                    log_entities_path, result["unique_spacy_entities"]
                )
            if mapping_output_path:
                self.writer.write_mapping_file(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    result["mapping_dict_spacy"],
                    result["unique_spacy_entities"],
                )

        return self._success_response(
            "Anonymization complete",
            result["unique_spacy_entities"],
            result.get("replacements_map_spacy"),
            output_path,
        )

    async def anonymize_async(
        self,
        input_path: Path,
        output_path: Optional[Path],
        entities: Optional[List[str]],
        dry_run: bool,
        log_entities_path: Optional[Path],
        mapping_output_path: Optional[Path],
        **kwargs,
    ) -> Dict[str, Any]:
        self.audit_logger.reset()
        self.custom_rules_processor.reset()
        self.writer = AnonymizedFileWriter(dry_run)

        ext = input_path.suffix.lower()
        try:
            processor = FileProcessorFactory.get_processor(ext)
        except ValueError as e:
            return self._error_response(e)

        logger.debug(
            f"DEBUG (Engine Async): Processing {input_path} with {type(processor).__name__}"
        )

        extract_kwargs = {}
        if hasattr(processor, "has_header") and "has_header" in kwargs:
            extract_kwargs["has_header"] = kwargs["has_header"]

        original_blocks = await processor.extract_blocks_async(
            input_path, **extract_kwargs
        )

        # Appel Logique Métier (identique au sync)
        result = self._process_content(original_blocks)
        decision = result["decision"]

        if decision == "empty":
            logger.info("INFO (Engine Async): Contenu vide.")
            if not dry_run and output_path:
                await self.writer.write_anonymized_file_async(
                    processor, output_path, [], input_path, **kwargs
                )
            if mapping_output_path and not dry_run:
                await self.writer.write_mapping_file_async(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    {},
                    [],
                )
            return self._success_response("Input empty", [])

        elif decision == "no_changes":
            logger.info("INFO (Engine Async): Aucune modification requise.")
            if not dry_run and output_path:
                await self.writer.write_anonymized_file_async(
                    processor,
                    output_path,
                    result["blocks_after_custom"],
                    input_path,
                    **kwargs,
                )
            if mapping_output_path and not dry_run:
                await self.writer.write_mapping_file_async(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    {},
                    [],
                )
            return self._success_response("No changes applied", [])

        # Cas nominal
        if not dry_run:
            await self.writer.write_anonymized_file_async(
                processor=processor,
                output_path=output_path,
                final_processed_blocks=result["final_blocks"],
                original_input_path=input_path,
                spacy_entities_per_block_with_offsets=result[
                    "spacy_entities_per_block"
                ],
                **kwargs,
            )
            if log_entities_path:
                await self.writer.write_log_entities_file_async(
                    log_entities_path, result["unique_spacy_entities"]
                )
            if mapping_output_path:
                await self.writer.write_mapping_file_async(
                    mapping_output_path,
                    self.custom_rules_processor.get_custom_replacements_mapping(),
                    result["mapping_dict_spacy"],
                    result["unique_spacy_entities"],
                )

        return self._success_response(
            "Anonymization complete",
            result["unique_spacy_entities"],
            result.get("replacements_map_spacy"),
            output_path,
        )

    def _error_response(self, error):
        return {
            "status": "error",
            "error": str(error),
            "audit_log": self.audit_logger.summary(),
            "total_replacements": self.audit_logger.total(),
        }

    def _success_response(self, message, entities, replacements=None, output_path=None):
        return {
            "status": "success",
            "message": message,
            "entities_detected": entities,
            "output_path": str(output_path) if output_path else None,
            "replacements_applied_spacy": replacements,
            "audit_log": self.audit_logger.summary(),
            "total_replacements": self.audit_logger.total(),
        }
