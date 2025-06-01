# anonyfiles/anonyfiles_cli/anonymizer/anonyfiles_core.py

import re
import csv # Import du module CSV
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer

# Imports depuis les modules de votre projet
from .spacy_engine import SpaCyEngine
# Importer les constantes REGEX directement depuis le module .spacy_engine
from .spacy_engine import EMAIL_REGEX, DATE_REGEX, PHONE_REGEX, IBAN_REGEX
from .replacer import ReplacementSession
from .txt_processor import TxtProcessor
from .csv_processor import CsvProcessor
from .word_processor import DocxProcessor
from .excel_processor import ExcelProcessor
from .pdf_processor import PdfProcessor
from .json_processor import JsonProcessor

from .utils import apply_positional_replacements
from .audit import AuditLogger

PROCESSOR_MAP = {
    ".txt": TxtProcessor,
    ".csv": CsvProcessor,
    ".docx": DocxProcessor,
    ".xlsx": ExcelProcessor,
    ".pdf": PdfProcessor,
    ".json": JsonProcessor,
}

class AnonyfilesEngine:
    def __init__(self, config: Dict[str, Any],
                 exclude_entities_cli: Optional[List[str]] = None,
                 custom_replacement_rules: Optional[List[Dict[str, str]]] = None):
        self.config = config or {}
        model = self.config.get("spacy_model", "fr_core_news_md")
        self.engine = SpaCyEngine(model=model) # Instance de SpaCyEngine
        self.entities_exclude = set()
        self.entities_exclude.update(self.config.get("exclude_entities", []))

        mapping_gui_keys = {
            "anonymizePersons": "PER",
            "anonymizeLocations": "LOC",
            "anonymizeOrgs": "ORG",
            "anonymizeEmails": "EMAIL",
            "anonymizeDates": "DATE",
            "anonymizeMisc": "MISC",
            "anonymizePhones": "PHONE",
            "anonymizeIbans": "IBAN",
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

        self.custom_rules = custom_replacement_rules or []
        self.audit_logger = AuditLogger()
        self.custom_replacements_count = 0

        typer.echo(f"DEBUG (Engine Init): Entités spaCy activées initialement : {self.enabled_labels}")
        typer.echo(f"DEBUG (Engine Init): Entités à exclure (config + CLI) : {self.entities_exclude}")
        if self.custom_rules:
            typer.echo(f"DEBUG (Engine Init): Initialisé avec {len(self.custom_rules)} règle(s) personnalisée(s).")

    def _apply_custom_rules_to_block(self, text_block: str) -> str:
        if not self.custom_rules:
            return text_block

        modified_text = text_block
        for rule in self.custom_rules:
            pattern_str = rule.get("pattern")
            replacement = rule.get("replacement", "[CUSTOM_REDACTED]")
            is_regex = rule.get("isRegex", False)
            
            if not pattern_str:
                continue

            try:
                if is_regex:
                    new_text, n_repl = re.subn(pattern_str, replacement, modified_text, flags=re.IGNORECASE)
                else:
                    # Correction pour que le remplacement de texte simple ne se fasse que sur des mots entiers si possible,
                    # mais re.escape est plus sûr pour éviter les erreurs de regex si le pattern contient des caractères spéciaux.
                    # L'utilisation de \b peut être problématique si pattern_str contient des non-alphanumériques.
                    # On garde re.escape pour la robustesse, le \b peut être ajouté si besoin spécifique.
                    pattern_escaped_for_regex = re.escape(pattern_str) 
                    new_text, n_repl = re.subn(pattern_escaped_for_regex, replacement, modified_text, flags=re.IGNORECASE)


                if n_repl > 0:
                    self.audit_logger.log(pattern_str, replacement, "custom_regex" if is_regex else "custom_text", n_repl)
                    self.custom_replacements_count += n_repl
                modified_text = new_text
            except re.error as e:
                typer.echo(f"AVERTISSEMENT (Moteur): Regex invalide pour la règle personnalisée '{pattern_str}': {e}. Règle ignorée.", err=True)
        return modified_text

    def anonymize(self, input_path: Path, output_path: Optional[Path],
                  entities: Optional[List[str]],
                  dry_run: bool,
                  log_entities_path: Optional[Path],
                  mapping_output_path: Optional[Path],
                  **kwargs):

        self.audit_logger.reset()
        self.custom_replacements_count = 0

        ext = input_path.suffix.lower()
        processor_class = PROCESSOR_MAP.get(ext)

        typer.echo(f"DEBUG (Engine): Type de processor choisi : {processor_class.__name__ if processor_class else 'None'} pour extension {ext}")

        if not processor_class:
            return {"status": "error", "error": f"Type de fichier non supporté: {ext}", "audit_log": self.audit_logger.summary(), "total_replacements": self.audit_logger.total()}

        processor = processor_class()

        extract_kwargs = {}
        if isinstance(processor, CsvProcessor) and 'has_header' in kwargs:
            extract_kwargs['has_header'] = kwargs['has_header']
        original_blocks = processor.extract_blocks(input_path, **extract_kwargs)

        blocks_after_custom_rules = []
        if self.custom_rules:
            typer.echo(f"DEBUG (Engine): Application des règles personnalisées sur {len(original_blocks)} bloc(s) pour processeur {processor_class.__name__}.")
            for idx, block_text in enumerate(original_blocks):
                mod_block = self._apply_custom_rules_to_block(block_text)
                blocks_after_custom_rules.append(mod_block)
            if self.custom_replacements_count > 0:
                 typer.echo(f"DEBUG (Engine): Nombre total de remplacements personnalisés effectués : {self.custom_replacements_count}")
        else:
            blocks_after_custom_rules = original_blocks
        
        if not any(block.strip() for block in blocks_after_custom_rules):
            typer.echo("INFO (Engine): Contenu vide après application des règles personnalisées (ou initialement vide).")
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                # CORRECTION 1 ICI : Utilisation de 'input_path'
                processor.reconstruct_and_write_anonymized_file(output_path, [], input_path, **kwargs)

            if mapping_output_path and not dry_run:
                mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mapping_output_path, "w", encoding="utf-8", newline='') as f_map:
                    map_writer = csv.writer(f_map)
                    map_writer.writerow(["anonymized", "original", "label"])
            return {
                "status": "success", "message": "Input effectively empty, no spaCy processing.",
                "entities_detected": [], "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        all_spacy_entities_from_modified_blocks = []
        spacy_entities_per_block_with_offsets = []

        final_enabled_labels_for_spacy = self.enabled_labels - self.entities_exclude
        typer.echo(f"DEBUG (Engine): Labels spaCy effectivement activés pour la détection : {final_enabled_labels_for_spacy}")

        for block_text_processed_by_custom in blocks_after_custom_rules:
            if block_text_processed_by_custom.strip():
                doc = self.engine.nlp_doc(block_text_processed_by_custom)
                current_block_entities_with_offsets_spacy = []
                
                for ent in doc.ents:
                    if ent.label_ in final_enabled_labels_for_spacy:
                        all_spacy_entities_from_modified_blocks.append((ent.text, ent.label_))
                        current_block_entities_with_offsets_spacy.append((ent.text, ent.label_, ent.start_char, ent.end_char))
                
                regex_sources = {
                    "EMAIL": EMAIL_REGEX,
                    "DATE": DATE_REGEX,
                    "PHONE": PHONE_REGEX,
                    "IBAN": IBAN_REGEX
                }
                for label, pattern in regex_sources.items():
                    if label in final_enabled_labels_for_spacy:
                        for match in re.finditer(pattern, block_text_processed_by_custom, re.IGNORECASE if label == "DATE" else 0):
                            match_text = match.group(0)
                            is_duplicate_span = any(
                                m_start == match.start() and m_end == match.end()
                                for _, _, m_start, m_end in current_block_entities_with_offsets_spacy
                            )
                            if not is_duplicate_span:
                                all_spacy_entities_from_modified_blocks.append((match_text, label))
                                current_block_entities_with_offsets_spacy.append((match_text, label, match.start(), match.end()))
                
                spacy_entities_per_block_with_offsets.append(current_block_entities_with_offsets_spacy)
            else:
                spacy_entities_per_block_with_offsets.append([])
        
        temp_unique_map = {}
        for entity_text, label in all_spacy_entities_from_modified_blocks:
            is_regex_label = label in {"EMAIL", "DATE", "PHONE", "IBAN"}
            if entity_text not in temp_unique_map or \
               (is_regex_label and not (temp_unique_map[entity_text][0] in {"EMAIL", "DATE", "PHONE", "IBAN"})):
                temp_unique_map[entity_text] = (label, "spacy_or_regex")
        
        unique_spacy_entities = [(text, data[0]) for text, data in temp_unique_map.items()]

        if entities:
            typer.echo(f"DEBUG (Engine): Filtrage par la liste d'entités fournie en argument : {entities}")
            unique_spacy_entities = [(t, l) for t, l in unique_spacy_entities if l in set(entities)]

        typer.echo(f"DEBUG (Engine): Entités spaCy uniques (après détection et filtres) à traiter : {len(unique_spacy_entities)}")

        if not unique_spacy_entities and self.custom_replacements_count == 0:
            typer.echo("INFO (Engine): Aucune entité spaCy à anonymiser et aucune règle personnalisée n'a été appliquée.")
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                # CORRECTION 2 ICI : Utilisation de 'input_path'
                processor.reconstruct_and_write_anonymized_file(output_path, blocks_after_custom_rules, input_path, **kwargs) # Changé 'original_input_path' en 'input_path'

            if mapping_output_path and not dry_run:
                mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mapping_output_path, "w", encoding="utf-8", newline='') as f_map:
                    map_writer = csv.writer(f_map)
                    map_writer.writerow(["anonymized", "original", "label"])
            return {
                "status": "success", "message": "No spaCy entities found to anonymize and no custom rules applied.",
                "entities_detected": [], "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        replacement_rules_spacy_config = self.config.get("replacements", {})
        session = ReplacementSession()
        replacements_map_spacy, mapping_dict_spacy = session.generate_replacements(unique_spacy_entities, replacement_rules=replacement_rules_spacy_config)

        for original, code in mapping_dict_spacy.items():
            label = next((lbl for txt, lbl in unique_spacy_entities if txt == original), "UNKNOWN_SPACY_LABEL")
            # Compter les occurrences dans les blocs *après* les règles custom, car c'est ce texte qui sera traité par spaCy.
            n_repl_spacy_in_block = 0
            for block_idx, block_text_after_custom in enumerate(blocks_after_custom_rules):
                # Obtenir les entités spaCy spécifiques à ce bloc (celles qui seront effectivement remplacées)
                entities_in_this_block_to_replace_offsets = spacy_entities_per_block_with_offsets[block_idx]
                for ent_text_offset, ent_label_offset, _, _ in entities_in_this_block_to_replace_offsets:
                    if ent_text_offset == original and ent_label_offset == label:
                        n_repl_spacy_in_block += 1 # Compte chaque instance qui sera remplacée

            if n_repl_spacy_in_block > 0 : # Modifié pour utiliser le compte précis
                 self.audit_logger.log(original, code, f"spacy_{label}", n_repl_spacy_in_block)


        truly_final_blocks_for_processor = []
        if unique_spacy_entities:
            for i, block_text_after_custom in enumerate(blocks_after_custom_rules):
                entities_in_this_block_to_replace = spacy_entities_per_block_with_offsets[i]
                
                unique_spacy_entities_tuples = set(unique_spacy_entities) # Contient (text, label)

                # Filtrer pour ne garder que les entités (avec leurs offsets) qui sont dans la liste unique_spacy_entities
                # et qui doivent donc être remplacées par les codes spaCy.
                filtered_entities_for_replacement_in_block = [
                    ent_offset for ent_offset in entities_in_this_block_to_replace
                    if (ent_offset[0], ent_offset[1]) in unique_spacy_entities_tuples
                ]

                if block_text_after_custom.strip() and filtered_entities_for_replacement_in_block:
                    fully_anonymized_block = apply_positional_replacements(
                        block_text_after_custom,
                        replacements_map_spacy, # Le map des remplacements spaCy {original_text: replacement_code}
                        filtered_entities_for_replacement_in_block # Liste des (text, label, start, end) pour ce bloc
                    )
                    truly_final_blocks_for_processor.append(fully_anonymized_block)
                else:
                    truly_final_blocks_for_processor.append(block_text_after_custom)
        else:
            truly_final_blocks_for_processor = blocks_after_custom_rules

        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            typer.echo(f"DEBUG (Engine): Appel de reconstruct_and_write_anonymized_file pour {processor_class.__name__}")
            
            processor_specific_kwargs = {**kwargs}
            if isinstance(processor, PdfProcessor):
                processor_specific_kwargs["spacy_entities_on_custom_text_per_block"] = spacy_entities_per_block_with_offsets

            # Le troisième argument doit être le chemin du fichier original pour la structure,
            # qui est 'input_path' dans le contexte de cette méthode 'anonymize'.
            processor.reconstruct_and_write_anonymized_file(
                output_path=output_path,
                final_processed_blocks=truly_final_blocks_for_processor,
                original_input_path=input_path, 
                **processor_specific_kwargs
            )

        if log_entities_path and not dry_run:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8", newline='') as f_log:
                log_writer = csv.writer(f_log)
                log_writer.writerow(["Entite", "Label"])
                for t, l in unique_spacy_entities:
                    log_writer.writerow([t, l])

        if mapping_output_path and not dry_run:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            typer.echo(f"DEBUG (Engine): Écriture du fichier mapping ici : {mapping_output_path}")
            with open(mapping_output_path, "w", encoding="utf-8", newline='') as f_map:
                map_writer = csv.writer(f_map)
                map_writer.writerow(["anonymized", "original", "label"])
                for original, code in mapping_dict_spacy.items():
                    # Retrouver le label associé à 'original' depuis unique_spacy_entities
                    label = next((lbl for txt, lbl in unique_spacy_entities if txt == original), "UNKNOWN_SPACY_LABEL")
                    map_writer.writerow([code, original, label])

        total_replacements_logged = self.audit_logger.total()
        typer.echo(f"INFO (Engine): Anonymisation terminée. Total des remplacements (custom + spaCy) enregistrés dans l'audit : {total_replacements_logged}")

        return {
            "status": "success",
            "entities_detected": unique_spacy_entities, # Contient (text, label)
            "output_path": str(output_path) if output_path and not dry_run else None,
            "replacements_applied_spacy": replacements_map_spacy, # Contient {original_text: replacement_code}
            "audit_log": self.audit_logger.summary(),
            "total_replacements": total_replacements_logged,
        }

# ... (Fin de la classe) ...