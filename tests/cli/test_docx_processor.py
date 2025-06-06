from anonyfiles_cli.anonymizer.word_processor import DocxProcessor
from docx import Document
from pathlib import Path
import tempfile, os

def test_extract_blocks_docx():
    tmp = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    doc = Document()
    doc.add_paragraph("Pierre est à Paris.")
    doc.add_paragraph("Ceci est un test.")
    doc.save(tmp.name)
    processor = DocxProcessor()
    blocks = processor.extract_blocks(tmp.name)
    assert len(blocks) == 2
    assert "Pierre" in blocks[0]

def test_reconstruct_and_write_anonymized_file_docx():
    tmp_in = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    tmp_out = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    doc = Document()
    doc.add_paragraph("Pierre à Paris.")
    doc.save(tmp_in.name)
    processor = DocxProcessor()

    blocks = processor.extract_blocks(tmp_in.name)
    final_blocks = [b.replace("Pierre", "NOM003").replace("Paris", "VILLE_Z") for b in blocks]

    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name),
        final_blocks,
        Path(tmp_in.name),
    )

    doc_result = Document(tmp_out.name)
    assert "NOM003" in doc_result.paragraphs[0].text
    assert "VILLE_Z" in doc_result.paragraphs[0].text
