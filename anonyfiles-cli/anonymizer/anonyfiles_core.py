from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from docx import Document

from .spacy_engine import SpaCyEngine
from .txt_processor import extract_text_from_txt, replace_entities_in_txt
from .csv_processor import extract_text_from_csv, replace_entities_in_csv
from .excel_processor import extract_text_from_excel, replace_entities_in_excel
from .word_processor import extract_text_from_docx, replace_entities_in_docx
from .replacer import ReplacementSession
from .utils import apply_positional_replacements

class AnonyfilesEngine:
    def __init__(self, config: Dict[str, Any], exclude_entities_cli: Optional[List[str]] = None):
        self.config = config or {}
        model = self.config.get("spacy_model", "fr_core_news_md")
        self.engine = SpaCyEngine(model=model)
        # Charge la liste d'exclusion depuis la config YAML
        self.entities_exclude = set(tuple(e) for e in self.config.get("exclude_entities", []))
        # Ajoute ce qui vient de la CLI (option --exclude-entity "Texte,Label")
        if exclude_entities_cli:
            self.entities_exclude.update(tuple(e.split(',')) for e in exclude_entities_cli)

    def anonymize_txt(self, input_path: Path, output_path: Optional[Path], entities: Optional[List[str]],
                      dry_run: bool, log_entities_path: Optional[Path], mapping_output_path: Optional[Path]):
        result = {"status": "error", "output_path": str(output_path) if output_path else None}
        if not input_path.exists():
            result["error"] = f"Fichier d’entrée non trouvé : {input_path}"
            return result

        text_content = extract_text_from_txt(input_path)
        if not text_content.strip():
            result["status"] = "success"
            if not dry_run and output_path:
                output_path.write_text("")
            result["entities_detected"] = []
            return result

        unique_entities = self.engine.detect_entities(text_content)
        if entities:
            unique_entities = [(t, l) for t, l in unique_entities if l in set(entities)]
        # Applique le filtre d’exclusion YAML/CLI
        unique_entities = [e for e in unique_entities if e not in self.entities_exclude]
        if not unique_entities:
            result["status"] = "success"
            if not dry_run and output_path:
                output_path.write_text(text_content)
            result["entities_detected"] = []
            return result

        entities_with_offsets = []
        for entity_text, label in unique_entities:
            start = 0
            while True:
                start = text_content.find(entity_text, start)
                if start == -1:
                    break
                end = start + len(entity_text)
                entities_with_offsets.append((entity_text, label, start, end))
                start = end

        session = ReplacementSession()
        replacements, person_code_map = session.generate_replacements(unique_entities)

        anonymized_text_content = apply_positional_replacements(text_content, replacements, entities_with_offsets)
        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(anonymized_text_content)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_entities:
                    f.write(f"{t},{l}\n")
            result["log_file"] = str(log_entities_path)

        if mapping_output_path and person_code_map:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Nom Original\n")
                for original, code in person_code_map.items():
                    f.write(f"{code},{original}\n")
            result["mapping_file"] = str(mapping_output_path)

        result.update({
            "status": "success",
            "entities_detected": unique_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements,
        })
        return result

    def anonymize_docx(self, input_path: Path, output_path: Optional[Path], entities: Optional[List[str]],
                       dry_run: bool, log_entities_path: Optional[Path], mapping_output_path: Optional[Path]):
        result = {"status": "error", "output_path": str(output_path) if output_path else None}
        if not input_path.exists():
            result["error"] = f"Fichier d’entrée non trouvé : {input_path}"
            return result

        paragraph_texts = extract_text_from_docx(input_path)
        if not any(p.strip() for p in paragraph_texts):
            result["status"] = "success"
            if not dry_run and output_path:
                Document().save(output_path)
            result["entities_detected"] = []
            return result

        all_entities = []
        entities_per_block_with_offsets = []
        for p_text in paragraph_texts:
            if p_text.strip():
                entities_in_p = self.engine.detect_entities(p_text)
                all_entities.extend(entities_in_p)
                block_offsets = []
                for entity_text, label in entities_in_p:
                    start = 0
                    while True:
                        start = p_text.find(entity_text, start)
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
            result["status"] = "success"
            if not dry_run and output_path:
                Document().save(output_path)
            result["entities_detected"] = []
            return result

        session = ReplacementSession()
        replacements, person_code_map = session.generate_replacements(unique_entities)
        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            replace_entities_in_docx(input_path, output_path, replacements, entities_per_block_with_offsets)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_entities:
                    f.write(f"{t},{l}\n")
            result["log_file"] = str(log_entities_path)

        if mapping_output_path and person_code_map:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Nom Original\n")
                for original, code in person_code_map.items():
                    f.write(f"{code},{original}\n")
            result["mapping_file"] = str(mapping_output_path)

        result.update({
            "status": "success",
            "entities_detected": unique_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements,
        })
        return result

    def anonymize_csv(self, input_path: Path, output_path: Optional[Path], entities: Optional[List[str]],
                      dry_run: bool, log_entities_path: Optional[Path], mapping_output_path: Optional[Path]):
        result = {"status": "error", "output_path": str(output_path) if output_path else None}
        if not input_path.exists():
            result["error"] = f"Fichier d’entrée non trouvé : {input_path}"
            return result

        import csv
        csv_data = []
        with open(input_path, mode='r', encoding='utf-8') as fin:
            reader = csv.reader(fin)
            for row in reader:
                csv_data.append([str(cell) for cell in row])
        if not any(cell.strip() for row in csv_data for cell in row):
            result["status"] = "success"
            if not dry_run and output_path:
                with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                    pass
            result["entities_detected"] = []
            return result

        all_entities = []
        entities_per_block_with_offsets = []
        for row in csv_data:
            row_offsets = []
            for cell_text in row:
                if cell_text.strip():
                    entities_in_cell = self.engine.detect_entities(cell_text)
                    all_entities.extend(entities_in_cell)
                    cell_offsets = []
                    for entity_text, label in entities_in_cell:
                        start = 0
                        while True:
                            start = cell_text.find(entity_text, start)
                            if start == -1:
                                break
                            end = start + len(entity_text)
                            cell_offsets.append((entity_text, label, start, end))
                            start = end
                    row_offsets.append(cell_offsets)
                else:
                    row_offsets.append([])
            entities_per_block_with_offsets.append(row_offsets)

        unique_entities = list(set(all_entities))
        if entities:
            unique_entities = [(t, l) for t, l in unique_entities if l in set(entities)]
        unique_entities = [e for e in unique_entities if e not in self.entities_exclude]
        if not unique_entities:
            result["status"] = "success"
            if not dry_run and output_path:
                with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                    pass
            result["entities_detected"] = []
            return result

        session = ReplacementSession()
        replacements, person_code_map = session.generate_replacements(unique_entities)
        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            replace_entities_in_csv(input_path, output_path, replacements, csv_data, entities_per_block_with_offsets)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_entities:
                    f.write(f"{t},{l}\n")
            result["log_file"] = str(log_entities_path)

        if mapping_output_path and person_code_map:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Nom Original\n")
                for original, code in person_code_map.items():
                    f.write(f"{code},{original}\n")
            result["mapping_file"] = str(mapping_output_path)

        result.update({
            "status": "success",
            "entities_detected": unique_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements,
        })
        return result

    def anonymize_xlsx(self, input_path: Path, output_path: Optional[Path], entities: Optional[List[str]],
                       dry_run: bool, log_entities_path: Optional[Path], mapping_output_path: Optional[Path]):
        result = {"status": "error", "output_path": str(output_path) if output_path else None}
        if not input_path.exists():
            result["error"] = f"Fichier d’entrée non trouvé : {input_path}"
            return result

        try:
            df = pd.read_excel(input_path)
        except Exception as e:
            result["error"] = f"Erreur de lecture Excel : {e}"
            return result

        if df.empty:
            result["status"] = "success"
            if not dry_run and output_path:
                df.to_excel(output_path, index=False)
            result["entities_detected"] = []
            return result

        all_entities = []
        entities_per_block_with_offsets = []
        cell_values = df.values.flatten()
        texts = [str(value) if pd.notna(value) else '' for value in cell_values]
        for cell_text in texts:
            if cell_text.strip():
                entities_in_cell = self.engine.detect_entities(cell_text)
                all_entities.extend(entities_in_cell)
                cell_offsets = []
                for entity_text, label in entities_in_cell:
                    start = 0
                    while True:
                        start = cell_text.find(entity_text, start)
                        if start == -1:
                            break
                        end = start + len(entity_text)
                        cell_offsets.append((entity_text, label, start, end))
                        start = end
                entities_per_block_with_offsets.append(cell_offsets)
            else:
                entities_per_block_with_offsets.append([])

        unique_entities = list(set(all_entities))
        if entities:
            unique_entities = [(t, l) for t, l in unique_entities if l in set(entities)]
        unique_entities = [e for e in unique_entities if e not in self.entities_exclude]
        if not unique_entities:
            result["status"] = "success"
            if not dry_run and output_path:
                df.to_excel(output_path, index=False)
            result["entities_detected"] = []
            return result

        session = ReplacementSession()
        replacements, person_code_map = session.generate_replacements(unique_entities)
        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            replace_entities_in_excel(input_path, output_path, replacements, df, entities_per_block_with_offsets)

        if log_entities_path:
            log_entities_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_entities_path, "w", encoding="utf-8") as f:
                f.write("Entite,Label\n")
                for t, l in unique_entities:
                    f.write(f"{t},{l}\n")
            result["log_file"] = str(log_entities_path)

        if mapping_output_path and person_code_map:
            mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_output_path, "w", encoding="utf-8") as f:
                f.write("Code,Nom Original\n")
                for original, code in person_code_map.items():
                    f.write(f"{code},{original}\n")
            result["mapping_file"] = str(mapping_output_path)

        result.update({
            "status": "success",
            "entities_detected": unique_entities,
            "output_path": str(output_path) if output_path else None,
            "replacements": replacements,
        })
        return result
