# anonyfiles_cli/anonymizer/engine.py

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .spacy_engine import SpaCyEngine
from .utils import apply_positional_replacements
from .audit import AuditLogger
from .custom_rules_processor import CustomRulesProcessor
from .ner_processor import NERProcessor
from .file_processor_factory import FileProcessorFactory
from .replacement_generator import ReplacementGenerator
from .writer import AnonymizedFileWriter
from .type_defs import EntityLabelOverrides, EntitySpansByBlock
from .privacy_warning_scanner import (
    privacy_warning_count,
    scan_blocks_for_privacy_warnings,
)

logger = logging.getLogger(__name__)

# Remplace les tokens {{...}} par des espaces de même longueur avant passage au NER.
# Évite que les accolades produites par les custom rules créent des faux positifs NER.
_CUSTOM_TOKEN_RE = re.compile(r"\{\{[^{}]+\}\}")


def _sanitize_for_ner(text: str) -> str:
    """Remplace {{TOKEN}} par des espaces de même longueur — préserve les offsets."""
    return _CUSTOM_TOKEN_RE.sub(lambda m: " " * len(m.group()), text)


def apply_entity_decisions_to_detected_entities(
    entities_per_block: EntitySpansByBlock,
    ignored_entity_texts: set[str] | None = None,
    entity_label_overrides: EntityLabelOverrides | None = None,
) -> tuple[list[tuple[str, str]], EntitySpansByBlock]:
    """Apply user preview decisions to detected entity spans.

    Decisions are keyed by exact entity text because the current preview UI
    exposes unique detected values rather than individual offsets.
    """
    ignored = ignored_entity_texts or set()
    label_overrides = entity_label_overrides or {}
    filtered_per_block: EntitySpansByBlock = []
    unique_by_text: dict[str, str] = {}

    for block_entities in entities_per_block:
        filtered_block = []
        for ent_text, ent_label, start, end in block_entities:
            if ent_text in ignored:
                continue
            final_label = label_overrides.get(ent_text, ent_label)
            filtered_block.append((ent_text, final_label, start, end))
            unique_by_text[ent_text] = final_label
        filtered_per_block.append(filtered_block)

    return list(unique_by_text.items()), filtered_per_block


def add_manual_entities_to_detected_entities(
    text_blocks: list[str],
    entities_per_block: EntitySpansByBlock,
    manual_entities: list[dict[str, str]] | None = None,
) -> tuple[list[tuple[str, str]], EntitySpansByBlock]:
    """Add exact user-provided entities to block spans without overlapping detections."""
    if not manual_entities:
        detected_unique_by_text: dict[str, str] = {}
        for block_entities in entities_per_block:
            for ent_text, ent_label, _start, _end in block_entities:
                detected_unique_by_text[ent_text] = ent_label
        return list(detected_unique_by_text.items()), entities_per_block

    enriched_per_block: EntitySpansByBlock = [
        list(block) for block in entities_per_block
    ]
    unique_by_text: dict[str, str] = {}

    for block_index, block_text in enumerate(text_blocks):
        block_entities = enriched_per_block[block_index]
        for manual_entity in manual_entities:
            text = manual_entity["text"]
            label = manual_entity["label"]
            search_start = 0
            while True:
                start = block_text.find(text, search_start)
                if start == -1:
                    break
                end = start + len(text)
                overlaps = any(
                    start < existing_end and end > existing_start
                    for *_entity, existing_start, existing_end in block_entities
                )
                if not overlaps:
                    block_entities.append((text, label, start, end))
                search_start = end

    for block_entities in enriched_per_block:
        block_entities.sort(key=lambda entity: entity[2])
        for ent_text, ent_label, _start, _end in block_entities:
            unique_by_text[ent_text] = ent_label

    return list(unique_by_text.items()), enriched_per_block


class AnonyfilesEngine:
    """
    Orchestre le processus complet d'anonymisation d'un fichier.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        exclude_entities_cli: Optional[List[str]] = None,
        custom_replacement_rules: Optional[List[Dict[str, str]]] = None,
        ignored_entity_texts: Optional[set[str]] = None,
        entity_label_overrides: Optional[Dict[str, str]] = None,
        manual_entities: Optional[List[Dict[str, str]]] = None,
        strict_mode: Optional[bool] = None,
    ):
        self.config = config or {}
        self.ignored_entity_texts = ignored_entity_texts or set()
        self.entity_label_overrides = entity_label_overrides or {}
        self.manual_entities = manual_entities or []
        self.strict_mode = bool(
            strict_mode
            if strict_mode is not None
            else self.config.get("strict_mode", self.config.get("strictMode", False))
        )

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
            self.spacy_engine,
            self.enabled_labels,
            self.entities_exclude,
            strict_mode=self.strict_mode,
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

    def _scan_privacy_warnings(
        self,
        final_blocks: List[str],
        ignored_values: list[str] | None = None,
    ) -> list[dict[str, object]]:
        return scan_blocks_for_privacy_warnings(
            final_blocks,
            enabled_labels=self.enabled_labels - self.entities_exclude,
            ignored_values=ignored_values or [],
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
            privacy_warnings = self._scan_privacy_warnings(blocks_after_custom_rules)
            return {
                "decision": "empty",
                "blocks_after_custom": blocks_after_custom_rules,
                "privacy_warnings": privacy_warnings,
            }

        # 2. Détection des entités spaCy et regex
        # Sanitisation : les tokens {{...}} sont remplacés par des espaces de même longueur
        # pour éviter que les accolades créent des faux positifs NER sur les spans adjacents.
        # Les offsets retournés restent valides dans blocks_after_custom_rules (même longueur).
        unique_spacy_entities, spacy_entities_per_block_with_offsets = (
            self.ner_processor.detect_entities_in_blocks(
                [_sanitize_for_ner(b) for b in blocks_after_custom_rules]
            )
        )
        unique_spacy_entities, spacy_entities_per_block_with_offsets = (
            apply_entity_decisions_to_detected_entities(
                spacy_entities_per_block_with_offsets,
                ignored_entity_texts=self.ignored_entity_texts,
                entity_label_overrides=self.entity_label_overrides,
            )
        )
        unique_spacy_entities, spacy_entities_per_block_with_offsets = (
            add_manual_entities_to_detected_entities(
                blocks_after_custom_rules,
                spacy_entities_per_block_with_offsets,
                self.manual_entities,
            )
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
            privacy_warnings = self._scan_privacy_warnings(blocks_after_custom_rules)
            return {
                "decision": "no_changes",
                "blocks_after_custom": blocks_after_custom_rules,
                "unique_spacy_entities": [],
                "privacy_warnings": privacy_warnings,
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

        ignored_replacement_values = list(replacements_map_spacy.values()) + list(
            self.custom_rules_processor.get_custom_replacements_mapping().values()
        )
        privacy_warnings = self._scan_privacy_warnings(
            truly_final_blocks,
            ignored_values=ignored_replacement_values,
        )

        return {
            "decision": "processed",
            "final_blocks": truly_final_blocks,
            "unique_spacy_entities": unique_spacy_entities,
            "spacy_entities_per_block": spacy_entities_per_block_with_offsets,
            "replacements_map_spacy": replacements_map_spacy,
            "mapping_dict_spacy": mapping_dict_spacy,
            "privacy_warnings": privacy_warnings,
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
        if ext == ".csv" and "has_header" in kwargs:
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
            return self._success_response(
                "Input empty", [], privacy_warnings=result["privacy_warnings"]
            )

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
            return self._success_response(
                "No changes applied", [], privacy_warnings=result["privacy_warnings"]
            )

        # Cas nominal: processed
        if not dry_run:
            if output_path is None:
                return self._error_response(
                    ValueError("output_path est requis hors dry-run.")
                )
            self.writer.write_anonymized_file(
                processor=processor,
                output_path=output_path,
                final_processed_blocks=result["final_blocks"],
                original_input_path=input_path,
                spacy_entities_per_block_with_offsets=result[
                    "spacy_entities_per_block"
                ],
                spacy_replacements_map=result["replacements_map_spacy"],
                custom_replacements_mapping=self.custom_rules_processor.get_custom_replacements_mapping(),
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
            result["privacy_warnings"],
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
        if ext == ".csv" and "has_header" in kwargs:
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
            return self._success_response(
                "Input empty", [], privacy_warnings=result["privacy_warnings"]
            )

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
            return self._success_response(
                "No changes applied", [], privacy_warnings=result["privacy_warnings"]
            )

        # Cas nominal
        if not dry_run:
            if output_path is None:
                return self._error_response(
                    ValueError("output_path est requis hors dry-run.")
                )
            await self.writer.write_anonymized_file_async(
                processor=processor,
                output_path=output_path,
                final_processed_blocks=result["final_blocks"],
                original_input_path=input_path,
                spacy_entities_per_block_with_offsets=result[
                    "spacy_entities_per_block"
                ],
                spacy_replacements_map=result["replacements_map_spacy"],
                custom_replacements_mapping=self.custom_rules_processor.get_custom_replacements_mapping(),
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
            result["privacy_warnings"],
        )

    def _error_response(self, error):
        return {
            "status": "error",
            "error": str(error),
            "audit_log": self.audit_logger.summary(),
            "total_replacements": self.audit_logger.total(),
        }

    def _success_response(
        self,
        message,
        entities,
        replacements=None,
        output_path=None,
        privacy_warnings=None,
    ):
        warnings = privacy_warnings or []
        return {
            "status": "success",
            "message": message,
            "entities_detected": entities,
            "output_path": str(output_path) if output_path else None,
            "replacements_applied_spacy": replacements,
            "audit_log": self.audit_logger.summary(),
            "total_replacements": self.audit_logger.total(),
            "privacy_warnings": warnings,
            "privacy_warnings_count": privacy_warning_count(warnings),
        }
