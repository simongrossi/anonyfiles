import pytest

pytest.importorskip("spacy")
import tempfile
import csv
from pathlib import Path

from anonyfiles_core.anonymizer.csv_processor import CsvProcessor


def test_extract_blocks_csv():
    with tempfile.NamedTemporaryFile(
        "w+", delete=False, encoding="utf-8", newline=""
    ) as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["Alice", "Paris"])
        writer.writerow(["Bob", "Lyon"])
        tmp.flush()
        processor = CsvProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert blocks == ["Alice", "Paris", "Bob", "Lyon"]


def test_reconstruct_and_write_anonymized_file_csv():
    with tempfile.NamedTemporaryFile(
        "w+", delete=False, encoding="utf-8", newline=""
    ) as tmp_in:
        writer = csv.writer(tmp_in)
        writer.writerow(["Alice", "Paris"])
        writer.writerow(["Bob", "Lyon"])
        tmp_in.flush()

        processor = CsvProcessor()
        blocks = processor.extract_blocks(Path(tmp_in.name))
        replacements = {
            "Alice": "NOM002",
            "Paris": "VILLE_Y",
            "Bob": "NAME003",
            "Lyon": "CITY_X",
        }
        final_blocks = [replacements.get(b, b) for b in blocks]

        with tempfile.NamedTemporaryFile(
            "r", delete=False, encoding="utf-8", newline=""
        ) as tmp_out:
            pass

        processor.reconstruct_and_write_anonymized_file(
            Path(tmp_out.name),
            final_blocks,
            Path(tmp_in.name),
        )

        with open(tmp_out.name, encoding="utf-8") as res:
            content = res.read()

        assert "NOM002" in content
        assert "VILLE_Y" in content
        assert "NAME003" in content
        assert "CITY_X" in content
