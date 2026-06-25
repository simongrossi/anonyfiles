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
        Path(tmp_out.name),
        final_blocks,
        Path(tmp_in.name),
        spacy_replacements_map={"Pierre": "NOM001", "Paris": "VILLE_X"},
    )

    res_doc = fitz.open(tmp_out.name)
    page_text = res_doc[0].get_text("text").strip()
    assert "NOM001" in page_text
    assert "VILLE_X" in page_text
    assert "Pierre" not in page_text
    assert "Paris" not in page_text


def test_pdf_redaction_removes_sensitive_text_from_extractable_layer():
    PdfReader = pytest.importorskip("pypdf").PdfReader
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    create_simple_pdf(Path(tmp_in.name), "Jean Dupont contact jean@example.com")

    processor = PdfProcessor()
    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name),
        ["PER_1 contact EMAIL_1"],
        Path(tmp_in.name),
        spacy_replacements_map={
            "Jean Dupont": "PER_1",
            "jean@example.com": "EMAIL_1",
        },
    )

    res_doc = fitz.open(tmp_out.name)
    pymupdf_text = res_doc[0].get_text("text")
    pypdf_text = PdfReader(tmp_out.name).pages[0].extract_text()

    combined_text = f"{pymupdf_text}\n{pypdf_text}"
    assert "Jean Dupont" not in combined_text
    assert "jean@example.com" not in combined_text
    assert "PER_1" in combined_text
    assert "EMAIL_1" in combined_text
