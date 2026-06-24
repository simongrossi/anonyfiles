import pytest

Document = pytest.importorskip("docx").Document
from anonyfiles_core.anonymizer.word_processor import DocxProcessor  # noqa: E402
from pathlib import Path  # noqa: E402
import tempfile  # noqa: E402


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
    final_blocks = [
        b.replace("Pierre", "NOM003").replace("Paris", "VILLE_Z") for b in blocks
    ]

    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name),
        final_blocks,
        Path(tmp_in.name),
    )

    doc_result = Document(tmp_out.name)
    assert "NOM003" in doc_result.paragraphs[0].text
    assert "VILLE_Z" in doc_result.paragraphs[0].text


def test_reconstruct_and_write_anonymized_file_docx_preserves_formatting():
    tmp_in = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    tmp_out = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")

    doc = Document()
    p = doc.add_paragraph()
    r1 = p.add_run("Pierre")
    r1.bold = True
    p.add_run(" à ")
    r3 = p.add_run("Paris")
    r3.italic = True
    doc.save(tmp_in.name)

    processor = DocxProcessor()
    blocks = processor.extract_blocks(tmp_in.name)
    final_blocks = [
        b.replace("Pierre", "NOM003").replace("Paris", "VILLE_Z") for b in blocks
    ]

    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name),
        final_blocks,
        Path(tmp_in.name),
    )

    doc_result = Document(tmp_out.name)
    runs = doc_result.paragraphs[0].runs
    assert runs[0].text == "NOM003"
    assert runs[0].bold
    assert runs[-1].text.endswith("VILLE_Z")
    assert runs[-1].italic


def test_docx_header_and_footer_are_anonymized():
    tmp_in = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    tmp_out = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")

    doc = Document()
    doc.add_paragraph("Corps avec Pierre.")
    section = doc.sections[0]
    # Écrire dans l'en-tête et le pied de page les délie automatiquement.
    section.header.paragraphs[0].text = "En-tête: Jean Dupont"
    section.footer.paragraphs[0].text = "Pied: Marie Curie"
    doc.save(tmp_in.name)

    processor = DocxProcessor()
    blocks = processor.extract_blocks(tmp_in.name)

    # Le contenu des en-têtes/pieds de page doit être extrait.
    assert any("Jean Dupont" in b for b in blocks)
    assert any("Marie Curie" in b for b in blocks)

    final_blocks = [
        b.replace("Jean Dupont", "PER_HEADER")
        .replace("Marie Curie", "PER_FOOTER")
        .replace("Pierre", "PER_BODY")
        for b in blocks
    ]
    processor.reconstruct_and_write_anonymized_file(
        Path(tmp_out.name),
        final_blocks,
        Path(tmp_in.name),
    )

    result = Document(tmp_out.name)
    assert "PER_BODY" in result.paragraphs[0].text
    assert "PER_HEADER" in result.sections[0].header.paragraphs[0].text
    assert "PER_FOOTER" in result.sections[0].footer.paragraphs[0].text


def test_extract_blocks_invalid_docx_raises_clear_error():
    tmp = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    tmp.write(b"this is not a real docx file")
    tmp.flush()
    tmp.close()

    processor = DocxProcessor()
    with pytest.raises(ValueError, match="docx"):
        processor.extract_blocks(tmp.name)


def test_reconstruct_and_write_anonymized_file_docx_mismatch():
    tmp_in = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    tmp_out = tempfile.NamedTemporaryFile("w+b", delete=False, suffix=".docx")
    doc = Document()
    doc.add_paragraph("Texte unique")
    doc.save(tmp_in.name)

    processor = DocxProcessor()

    # Fournir une liste vide pour provoquer un décalage de compte
    with pytest.raises(ValueError):
        processor.reconstruct_and_write_anonymized_file(
            Path(tmp_out.name),
            [],
            Path(tmp_in.name),
        )
