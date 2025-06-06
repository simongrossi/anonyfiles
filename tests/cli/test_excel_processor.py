import tempfile
import pandas as pd
from anonyfiles_cli.anonymizer.excel_processor import ExcelProcessor
from pathlib import Path

def test_extract_blocks_excel():
    tmp = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".xlsx")
    df = pd.DataFrame({"A": ["Alice", "Bob"], "B": ["Paris", "Lyon"]})
    df.to_excel(tmp.name, index=False)
    processor = ExcelProcessor()
    blocks = processor.extract_blocks(tmp.name)
    assert "Alice" in blocks and "Paris" in blocks

def test_reconstruct_and_write_anonymized_file_excel():
    tmp_in = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".xlsx")
    tmp_out = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".xlsx")
    df = pd.DataFrame({"A": ["Alice"], "B": ["Paris"]})
    df.to_excel(tmp_in.name, index=False)
    processor = ExcelProcessor()
    blocks = processor.extract_blocks(tmp_in.name)
    final_blocks = [b.replace("Alice", "NOM004").replace("Paris", "VILLE_W") for b in blocks]
    processor.reconstruct_and_write_anonymized_file(Path(tmp_out.name), final_blocks, Path(tmp_in.name))
    result = pd.read_excel(tmp_out.name)
    assert "NOM004" in result.values
    assert "VILLE_W" in result.values
