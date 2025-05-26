# anonyfiles_cli/anonymizer/anonyfiles_core.py

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer

from .spacy_engine import SpaCyEngine
from .replacer import ReplacementSession
from .txt_processor import TxtProcessor
from .csv_processor import CsvProcessor
# from .word_processor import DocxProcessor
# from .excel_processor import ExcelProcessor
# from .pdf_processor import PdfProcessor
# from .json_processor import JsonProcessor

from docx import Document
import pandas as pd
from .utils import apply_positional_replacements

from .audit import AuditLogger

PROCESSOR_MAP = {
    ".txt": TxtProcessor,
    # ".csv": CsvProcessor,
    # ".docx": DocxProcessor,
    # ".xlsx": ExcelProcessor,
    # ".pdf": PdfProcessor,
    # ".json": JsonProcessor,
}

class AnonyfilesEngine:
    def __init__(self, config: Dict[str, Any],
                 exclude_entities_cli: Optional[List[str]] = None,
                 custom_replacement_rules: Optional[List[Dict[str, str]]] = None):
        self.config = config or {}
        model = self.config.get("spacy_model", "fr_core_news_md")
        self.engine = SpaCyEngine(model=model)
        self.entities_exclude = set()
        self.entities_exclude.update(self.config.get("exclude_entities", []))
        if exclude_entities_cli:
            for e in exclude_entities_cli:
                self.entities_exclude.update(e.split(","))
        self.custom_rules = custom_replacement_rules or []
        self.audit_logger = AuditLogger()  # Ajout audit logger
        typer.echo(f"DEBUG (Engine): Entités à exclure (spaCy) : {self.entities_exclude}")
        if self.custom_rules:
            typer.echo(f"DEBUG (Engine): Initialisé avec {len(self.custom_rules)} règle(s) personnalisée(s).")

    def _apply_custom_rules_to_block(self, text_block: str) -> str:
        """
        Applique les règles de remplacement personnalisées à un bloc de texte et loggue les remplacements.
        Prend en charge les règles en regex et les remplacements de mots entiers, insensible à la casse.
        Ajoute des logs de debug.
        """
        if not self.custom_rules:
            return text_block

        modified_text = text_block
        for rule in self.custom_rules:
            pattern = rule.get("pattern")
            replacement = rule.get("replacement", "[CUSTOM_REDACTED]")
            is_regex = rule.get("isRegex", False)
            if pattern:
                try:
                    if is_regex:
                        new_text, n_repl = re.subn(pattern, replacement, modified_text, flags=re.IGNORECASE)
                    else:
                        pattern_escaped = r"\b" + re.escape(pattern) + r"\b"
                        new_text, n_repl = re.subn(pattern_escaped, replacement, modified_text, flags=re.IGNORECASE)
                    if n_repl > 0:
                        typer.echo(f"[CUSTOM_RULE] Pattern '{pattern}' trouvé et remplacé {n_repl} fois dans bloc : {repr(modified_text)}")
                        self.audit_logger.log(pattern, replacement, "custom", n_repl)
                    modified_text = new_text
                except re.error as e:
                    typer.echo(f"AVERTISSEMENT (Moteur): Regex invalide pour la règle personnalisée '{pattern}': {e}. Règle ignorée.", err=True)
        return modified_text

    def anonymize(self, input_path: Path, output_path: Optional[Path],
                  entities: Optional[List[str]],
                  dry_run: bool,
                  log_entities_path: Optional[Path],
                  mapping_output_path: Optional[Path],
                  **kwargs):

        ext = input_path.suffix.lower()
        processor_class = PROCESSOR_MAP.get(ext)
        if not processor_class:
            return {"status": "error", "error": f"Type de fichier non supporté: {ext}"}

        processor = processor_class()

        extract_kwargs = {}
        if isinstance(processor, CsvProcessor) and 'has_header' in kwargs:
            extract_kwargs['has_header'] = kwargs['has_header']
        original_blocks = processor.extract_blocks(input_path, **extract_kwargs)

        # 1. Application des règles custom (log + modif blocs)
        blocks_after_custom_rules = []
        if isinstance(processor, TxtProcessor) and self.custom_rules:
            typer.echo(f"DEBUG (Engine): Application des règles personnalisées sur {len(original_blocks)} bloc(s) TXT.")
            for block in original_blocks:
                typer.echo(f"[DEBUG] Bloc avant custom : {repr(block)}")
                mod_block = self._apply_custom_rules_to_block(block)
                typer.echo(f"[DEBUG] Bloc après custom : {repr(mod_block)}")
                blocks_after_custom_rules.append(mod_block)
        else:
            if self.custom_rules and not isinstance(processor, TxtProcessor):
                typer.echo(f"AVERTISSEMENT (Engine): Règles personnalisées non appliquées pour le type {ext} dans cette version.", err=True)
            blocks_after_custom_rules = original_blocks

        # 2. Traitement spaCy sur ces blocs
        if not any(block.strip() for block in blocks_after_custom_rules):
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(processor, TxtProcessor):
                    getattr(processor, 'write_final_blocks', lambda o, b, **kw: o.write_text(""))(output_path, [])
                elif ext == ".xlsx":
                    pd.DataFrame().to_excel(output_path, index=False)
                elif ext == ".docx":
                    Document().save(output_path)
                else:
                    output_path.write_text("")
            if mapping_output_path:
                mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mapping_output_path, "w", encoding="utf-8") as f:
                    f.write("Code,Type,Nom Original\n")
            return {
                "status": "success",
                "entities_detected": [],
                "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        all_spacy_entities = []
        spacy_entities_per_block_with_offsets = []

        for block_text_processed in blocks_after_custom_rules:
            if block_text_processed.strip():
                entities_in_block_spacy = self.engine.detect_entities(block_text_processed)
                all_spacy_entities.extend(entities_in_block_spacy)
                current_block_offsets_spacy = []
                for entity_text, label in entities_in_block_spacy:
                    start = 0
                    while True:
                        start = block_text_processed.find(entity_text, start)
                        if start == -1:
                            break
                        end = start + len(entity_text)
                        current_block_offsets_spacy.append((entity_text, label, start, end))
                        start = end
                spacy_entities_per_block_with_offsets.append(current_block_offsets_spacy)
            else:
                spacy_entities_per_block_with_offsets.append([])

        unique_spacy_entities = list(set(all_spacy_entities))
        typer.echo(f"DEBUG - Entités uniques spaCy AVANT filtre exclusion : {unique_spacy_entities}")
        if entities:
            unique_spacy_entities = [(t, l) for t, l in unique_spacy_entities if l in set(entities)]
            typer.echo(f"DEBUG - Après filtre par liste 'entities' param : {unique_spacy_entities}")
        unique_spacy_entities = [e for e in unique_spacy_entities if e[1] not in self.entities_exclude]
        typer.echo(f"DEBUG - Entités uniques spaCy APRÈS filtre exclusion : {unique_spacy_entities}")

        # Si aucune entité spaCy à traiter, log uniquement les règles custom
        if not unique_spacy_entities:
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(processor, TxtProcessor):
                    processor.write_final_blocks(output_path, blocks_after_custom_rules)
                else:
                    import shutil
                    shutil.copyfile(input_path, output_path)
            if mapping_output_path:
                mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mapping_output_path, "w", encoding="utf-8") as f:
                    f.write("Code,Type,Nom Original\n")
            return {
                "status": "success",
                "entities_detected": [],
                "audit_log": self.audit_logger.summary(),
                "total_replacements": self.audit_logger.total(),
            }

        typer.echo(f"DEBUG - Entités spaCy uniques utilisées pour anonymisation : {unique_spacy_entities}")

        replacement_rules_spacy = self.config.get("replacements", {})
        session = ReplacementSession()
        replacements_map_spacy, mapping_dict_spacy = session.generate_replacements(unique_spacy_entities, replacement_rules=replacement_rules_spacy)

        # Audit des remplacements spaCy (par entité)
        for original, code in mapping_dict_spacy.items():
            label = next((lbl for txt, lbl in unique_spacy_entities if txt == original), "UNKNOWN")
            n_repl = sum(
                block.count(original)
                for block in blocks_after_custom_rules
            )
            self.audit_logger.log(original, code, "spacy", n_repl)

        final_anonymized_blocks = []
        for i, block_text_after_custom in enumerate(blocks_after_custom_rules):
            if block_text_after_custom.strip() and spacy_entities_per_block_with_offsets[i]:
                fully_anonymized_block = apply_positional_replacements(
                    block_text_after_custom,
                    replacements_map_spacy,
                    spacy_entities_per_block_with_offsets[i]
                )
                final_anonymized_blocks.append(fully_anonymized_block)
            else:
                final_anonymized_blocks.append(block_text_after_custom)

        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(processor, TxtProcessor):
                processor.write_final_blocks(output_path, final_anonymized_blocks)
            else:
                typer.echo(f"DEBUG (Engine): Utilisation de processor.replace_entities pour {ext}")
                processor.replace_entities(input_path, output_path, replacements_map_spacy, spacy_entities_per_block_with_offsets, **kwargs)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_spacy_entities:
                    f.write(f"{t},{l}\n")

        if mapping_output_path:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            typer.echo(f"DEBUG: Écriture du fichier mapping ici : {mapping_output_path}")
            typer.echo(f"DEBUG: Contenu mapping (spaCy) : {mapping_dict_spacy}")
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Type,Nom Original\n")
                for original, code in mapping_dict_spacy.items():
                    label = next((lbl for txt, lbl in unique_spacy_entities if txt == original), "UNKNOWN")
                    f.write(f"{code},{label},{original}\n")

        return {
            "status": "success",
            "entities_detected": unique_spacy_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements_map_spacy,
            "audit_log": self.audit_logger.summary(),
            "total_replacements": self.audit_logger.total(),
        }
