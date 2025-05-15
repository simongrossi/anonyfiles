# anonymizer/anonyfiles_core.py

from pathlib import Path
from typing import Optional, List, Dict, Any
from .spacy_engine import SpaCyEngine
from .replacer import ReplacementSession
from .txt_processor import TxtProcessor
from .csv_processor import CsvProcessor
from .word_processor import DocxProcessor
from .excel_processor import ExcelProcessor
from .pdf_processor import PdfProcessor
from .json_processor import JsonProcessor
import pandas as pd
from docx import Document

PROCESSOR_MAP = {
    ".txt": TxtProcessor,
    ".csv": CsvProcessor,
    ".docx": DocxProcessor,
    ".xlsx": ExcelProcessor,
    ".pdf": PdfProcessor,
    ".json": JsonProcessor,
}

class AnonyfilesEngine:
    def __init__(self, config: Dict[str, Any], exclude_entities_cli: Optional[List[str]] = None):
        self.config = config or {}
        model = self.config.get("spacy_model", "fr_core_news_md")
        self.engine = SpaCyEngine(model=model)
        self.entities_exclude = set(tuple(e) for e in self.config.get("exclude_entities", []))
        if exclude_entities_cli:
            self.entities_exclude.update(tuple(e.split(',')) for e in exclude_entities_cli)

    def anonymize(self, input_path: Path, output_path: Optional[Path], entities: Optional[List[str]],
                  dry_run: bool, log_entities_path: Optional[Path], mapping_output_path: Optional[Path]):

        ext = input_path.suffix.lower()
        processor_class = PROCESSOR_MAP.get(ext)
        if not processor_class:
            return {"status": "error", "error": f"Type de fichier non supporté: {ext}"}

        processor = processor_class()
        blocks = processor.extract_blocks(input_path)

        if not any(block.strip() for block in blocks):
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if ext == ".xlsx":
                    pd.DataFrame().to_excel(output_path, index=False)
                elif ext == ".docx":
                    Document().save(output_path)
                else:
                    output_path.write_text("")
            return {"status": "success", "entities_detected": []}

        all_entities = []
        entities_per_block_with_offsets = []
        for block_text in blocks:
            if block_text.strip():
                entities_in_block = self.engine.detect_entities(block_text)
                all_entities.extend(entities_in_block)
                block_offsets = []
                for entity_text, label in entities_in_block:
                    start = 0
                    while True:
                        start = block_text.find(entity_text, start)
                        if start == -1:
                            break
                        end = start + len(entity_text)
                        block_offsets.append((entity_text, label, start, end))
                        start = end
                entities_per_block_with_offsets.append(block_offsets)
            else:
                entities_per_block_with_offsets.append([])

        unique_entities = list(set(all_entities))
        if entities:
            unique_entities = [(t, l) for t, l in unique_entities if l in set(entities)]
        unique_entities = [e for e in unique_entities if e not in self.entities_exclude]

        if not unique_entities:
            if not dry_run and output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if ext == ".xlsx":
                    pd.DataFrame().to_excel(output_path, index=False)
                elif ext == ".docx":
                    Document().save(output_path)
                else:
                    output_path.write_text("")
            return {"status": "success", "entities_detected": []}

        session = ReplacementSession()
        replacements, person_code_map = session.generate_replacements(unique_entities)

        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            processor.replace_entities(input_path, output_path, replacements, entities_per_block_with_offsets)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_entities:
                    f.write(f"{t},{l}\n")

        if mapping_output_path and person_code_map:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Nom Original\n")
                for original, code in person_code_map.items():
                    f.write(f"{code},{original}\n")

        return {
            "status": "success",
            "entities_detected": unique_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements,
        }
