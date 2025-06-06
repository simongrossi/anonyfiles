import tempfile
from anonyfiles_cli.anonymizer.txt_processor import TxtProcessor
from pathlib import Path

def test_extract_blocks_simple():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("Bonjour Paris\nHello World")
        tmp.flush()
        processor = TxtProcessor()
        blocks = processor.extract_blocks(tmp.name)
        assert len(blocks) == 1
        assert "Bonjour Paris" in blocks[0]

def test_reconstruct_and_write_anonymized_file_txt():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_in, \
         tempfile.NamedTemporaryFile("r", delete=False, encoding="utf-8") as tmp_out:
        tmp_in.write("Pierre habite à Paris.")
        tmp_in.flush()
        processor = TxtProcessor()
        blocks = processor.extract_blocks(tmp_in.name)
        final_blocks = [b.replace("Pierre", "NOM001").replace("Paris", "VILLE_X") for b in blocks]
        processor.reconstruct_and_write_anonymized_file(Path(tmp_out.name), final_blocks, Path(tmp_in.name))
        result = tmp_out.read()
        assert "NOM001" in result
        assert "VILLE_X" in result
