import tempfile
from anonymizer.json_processor import JsonProcessor

def test_extract_blocks_json():
    content = '{"name": "Jean Dupont", "email": "jean.dupont@example.com"}'
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp.flush()
        processor = JsonProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert isinstance(blocks, list)
        assert len(blocks) == 1
        assert "Jean Dupont" in blocks[0]

def test_replace_entities_json():
    content = '{"name": "Jean Dupont", "email": "jean.dupont@example.com"}'
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8") as tmp_out:
        tmp_in.write(content)
        tmp_in.flush()
        processor = JsonProcessor()
        replacements = {"Jean Dupont": "NOM001", "jean.dupont@example.com": "EMAIL001"}
        entities_offsets = [[("Jean Dupont", "PER", 9, 19), ("jean.dupont@example.com", "EMAIL", 31, 53)]]
        processor.replace_entities(tmp_in.name, tmp_out.name, replacements, entities_offsets)
        result = tmp_out.read()
        assert "NOM001" in result
        assert "EMAIL001" in result
