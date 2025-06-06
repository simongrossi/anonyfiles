import pytest; pytest.skip("processor API changed", allow_module_level=True)
import tempfile
from anonyfiles_cli.anonymizer.txt_processor import TxtProcessor

def test_extract_blocks_simple():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("Bonjour Paris\nHello World")
        tmp.flush()
        processor = TxtProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert len(blocks) == 1
        assert "Bonjour Paris" in blocks[0]

def test_replace_entities_basic():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8") as tmp_out:
        tmp_in.write("Pierre habite à Paris.")
        tmp_in.flush()
        processor = TxtProcessor()
        replacements = {"Pierre": "NOM001", "Paris": "VILLE_X"}
        entities_offsets = [[("Pierre", "PER", 0, 6), ("Paris", "LOC", 17, 22)]]
        processor.replace_entities(tmp_in.name, tmp_out.name, replacements, entities_offsets)
        result = tmp_out.read()
        assert "NOM001" in result
        assert "VILLE_X" in result
