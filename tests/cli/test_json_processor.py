import tempfile
from anonyfiles_cli.anonymizer.json_processor import JsonProcessor
from pathlib import Path

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

def test_reconstruct_and_write_anonymized_file_json():
    content = '{"name": "Jean Dupont", "email": "jean.dupont@example.com"}'
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8") as tmp_out:
        tmp_in.write(content)
        tmp_in.flush()
        processor = JsonProcessor()
        blocks = processor.extract_blocks(tmp_in.name)
        final_blocks = [b.replace("Jean Dupont", "NOM001").replace("jean.dupont@example.com", "EMAIL001") for b in blocks]
        processor.reconstruct_and_write_anonymized_file(Path(tmp_out.name), final_blocks, Path(tmp_in.name))
        result = tmp_out.read()
        assert "NOM001" in result
        assert "EMAIL001" in result
