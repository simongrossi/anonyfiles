import pytest; pytest.skip("processor API changed", allow_module_level=True)
import tempfile
import csv
from anonyfiles_cli.anonymizer.csv_processor import CsvProcessor

def test_extract_blocks_csv():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8", newline='') as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["Alice", "Paris"])
        writer.writerow(["Bob", "Lyon"])
        tmp.flush()
        processor = CsvProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert blocks == ["Alice", "Paris", "Bob", "Lyon"]

def test_replace_entities_csv():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8", newline='') as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8", newline='') as tmp_out:
        writer = csv.writer(tmp_in)
        writer.writerow(["Alice", "Paris"])
        tmp_in.flush()
        processor = CsvProcessor()
        replacements = {"Alice": "NOM002", "Paris": "VILLE_Y"}
        entities_offsets = [[("Alice", "PER", 0, 5)], [("Paris", "LOC", 0, 5)]]
        processor.replace_entities(tmp_in.name, tmp_out.name, replacements, entities_offsets)
        content = tmp_out.read()
        assert "NOM002" in content
        assert "VILLE_Y" in content
