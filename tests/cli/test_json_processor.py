import pytest
pytest.importorskip("spacy")
import tempfile
from anonyfiles_core.anonymizer.json_processor import JsonProcessor
from pathlib import Path
import json


def _nested_sample() -> str:
    return json.dumps(
        {
            "name": "Jean Dupont",
            "contact": {
                "email": "jean.dupont@example.com",
                "phones": ["123", "456"],
            },
            "pets": [
                {"type": "dog", "name": "Rex"},
                "goldfish",
            ],
        }
    )


def test_extract_blocks_json():
    content = _nested_sample()
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp.flush()
        processor = JsonProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert isinstance(blocks, list)
        # 7 values should be extracted from the nested structure
        assert len(blocks) == 7
        assert "Jean Dupont" in blocks
        assert "jean.dupont@example.com" in blocks

def test_reconstruct_and_write_anonymized_file_json():
    content = _nested_sample()
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8") as tmp_out:
        tmp_in.write(content)
        tmp_in.flush()
        processor = JsonProcessor()
        blocks = processor.extract_blocks(tmp_in.name)

        replacements = {
            "Jean Dupont": "NOM001",
            "jean.dupont@example.com": "EMAIL001",
            "Rex": "PET001",
        }
        final_blocks = [replacements.get(b, b) for b in blocks]

        processor.reconstruct_and_write_anonymized_file(Path(tmp_out.name), final_blocks, Path(tmp_in.name))
        with open(tmp_out.name, encoding="utf-8") as res:
            result_json = json.load(res)

        assert result_json["name"] == "NOM001"
        assert result_json["contact"]["email"] == "EMAIL001"
        assert result_json["pets"][0]["name"] == "PET001"
        # keys should remain unchanged by default
        assert "name" in result_json
        assert "contact" in result_json
