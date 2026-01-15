import pytest

fitz = pytest.importorskip("fitz")
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from anonyfiles_core.anonymizer.pdf_processor import PdfProcessor  # noqa: E402


def create_simple_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)


def test_extract_blocks_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    create_simple_pdf(Path(tmp.name), "Pierre habite a Paris")

    processor = PdfProcessor()
    blocks = processor.extract_blocks(tmp.name)

    assert len(blocks) == 1
    assert "Pierre habite a Paris" in blocks[0]


def test_reconstruct_and_write_anonymized_file_pdf():
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    create_simple_pdf(Path(tmp_in.name), "Pierre habite a Paris")

    processor = PdfProcessor()
    blocks = processor.extract_blocks(tmp_in.name)
    final_blocks = [
        b.replace("Pierre", "NOM001").replace("Paris", "VILLE_X") for b in blocks
    ]

    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name), final_blocks, Path(tmp_in.name)
    )

    res_doc = fitz.open(tmp_out.name)
    page_text = res_doc[0].get_text("text").strip()
    assert "NOM001" in page_text
    assert "VILLE_X" in page_text
