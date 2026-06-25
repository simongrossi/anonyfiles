import csv
import json
from pathlib import Path

import pytest

from anonyfiles_core.anonymizer.csv_processor import CsvProcessor
from anonyfiles_core.anonymizer.json_processor import JsonProcessor
from anonyfiles_core.anonymizer.pdf_processor import PdfProcessor
from anonyfiles_core.anonymizer.txt_processor import TxtProcessor

SENSITIVE_VALUES = [
    "Jean Dupont",
    "Sophie Laurent",
    "jean.dupont@example.com",
    "sophie.laurent@example.fr",
    "06 12 34 56 78",
    "FR76 3000 6000 0112 3456 7890 189",
    "Beta Services",
    "Paris",
]


def _replace_blocks(blocks, replacements):
    anonymized_blocks = []
    for block in blocks:
        anonymized = block
        for original, replacement in replacements.items():
            anonymized = anonymized.replace(original, replacement)
        anonymized_blocks.append(anonymized)
    return anonymized_blocks


def _assert_no_sensitive_text(text, sensitive_values=None):
    values = sensitive_values or SENSITIVE_VALUES
    for sensitive in values:
        assert sensitive not in text


def test_txt_golden_snapshot(tmp_path):
    input_path = tmp_path / "sample.txt"
    output_path = tmp_path / "sample_anonymized.txt"
    input_path.write_text(
        "Client: Jean Dupont\n"
        "Email: jean.dupont@example.com\n"
        "Reference publique: EMAIL-2026\n",
        encoding="utf-8",
    )

    processor = TxtProcessor()
    blocks = processor.extract_blocks(input_path)
    final_blocks = _replace_blocks(
        blocks,
        {
            "Jean Dupont": "PER_TOKEN_1",
            "jean.dupont@example.com": "EMAIL_TOKEN_1",
        },
    )

    processor.reconstruct_and_write_anonymized_file(
        output_path, final_blocks, input_path
    )

    expected = (
        "Client: PER_TOKEN_1\n"
        "Email: EMAIL_TOKEN_1\n"
        "Reference publique: EMAIL-2026\n"
    )
    actual = output_path.read_text(encoding="utf-8")
    assert actual == expected
    _assert_no_sensitive_text(actual)


def test_csv_golden_snapshot_with_header(tmp_path):
    input_path = tmp_path / "sample.csv"
    output_path = tmp_path / "sample_anonymized.csv"
    with input_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["name", "email", "city"])
        writer.writerow(["Jean Dupont", "jean.dupont@example.com", "Paris"])
        writer.writerow(["Sophie Laurent", "sophie.laurent@example.fr", "Lyonnais"])

    processor = CsvProcessor()
    blocks = processor.extract_blocks(input_path, has_header=True)
    final_blocks = _replace_blocks(
        blocks,
        {
            "Jean Dupont": "PER_TOKEN_1",
            "Sophie Laurent": "PER_TOKEN_2",
            "jean.dupont@example.com": "EMAIL_TOKEN_1",
            "sophie.laurent@example.fr": "EMAIL_TOKEN_2",
            "Paris": "LOC_TOKEN_1",
        },
    )

    processor.reconstruct_and_write_anonymized_file(
        output_path, final_blocks, input_path, has_header=True
    )

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        actual_rows = list(csv.reader(csv_file))

    assert actual_rows == [
        ["name", "email", "city"],
        ["PER_TOKEN_1", "EMAIL_TOKEN_1", "LOC_TOKEN_1"],
        ["PER_TOKEN_2", "EMAIL_TOKEN_2", "Lyonnais"],
    ]
    _assert_no_sensitive_text(json.dumps(actual_rows, ensure_ascii=False))


def test_json_golden_snapshot_nested_values(tmp_path):
    input_path = tmp_path / "sample.json"
    output_path = tmp_path / "sample_anonymized.json"
    input_payload = {
        "employee": {
            "name": "Jean Dupont",
            "contact": {
                "email": "jean.dupont@example.com",
                "phone": "06 12 34 56 78",
            },
        },
        "company": "Beta Services",
        "tags": ["public", "EMAIL-2026"],
    }
    input_path.write_text(
        json.dumps(input_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    processor = JsonProcessor()
    blocks = processor.extract_blocks(input_path)
    final_blocks = _replace_blocks(
        blocks,
        {
            "Jean Dupont": "PER_TOKEN_1",
            "jean.dupont@example.com": "EMAIL_TOKEN_1",
            "06 12 34 56 78": "PHONE_TOKEN_1",
            "Beta Services": "ORG_TOKEN_1",
        },
    )

    processor.reconstruct_and_write_anonymized_file(
        output_path, final_blocks, input_path
    )

    actual = json.loads(output_path.read_text(encoding="utf-8"))
    assert actual == {
        "employee": {
            "name": "PER_TOKEN_1",
            "contact": {
                "email": "EMAIL_TOKEN_1",
                "phone": "PHONE_TOKEN_1",
            },
        },
        "company": "ORG_TOKEN_1",
        "tags": ["public", "EMAIL-2026"],
    }
    _assert_no_sensitive_text(json.dumps(actual, ensure_ascii=False))


def test_docx_golden_snapshot_body_table_header_footer(tmp_path):
    Document = pytest.importorskip("docx").Document
    from anonyfiles_core.anonymizer.word_processor import DocxProcessor

    input_path = tmp_path / "sample.docx"
    output_path = tmp_path / "sample_anonymized.docx"

    doc = Document()
    doc.add_paragraph("Contrat de Jean Dupont")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Email"
    table.cell(0, 1).text = "jean.dupont@example.com"
    table.cell(1, 0).text = "Ville"
    table.cell(1, 1).text = "Paris"
    section = doc.sections[0]
    section.header.paragraphs[0].text = "Confidentiel Sophie Laurent"
    section.footer.paragraphs[0].text = "Archive Beta Services"
    doc.save(input_path)

    processor = DocxProcessor()
    blocks = processor.extract_blocks(input_path)
    final_blocks = _replace_blocks(
        blocks,
        {
            "Jean Dupont": "PER_TOKEN_1",
            "Sophie Laurent": "PER_TOKEN_2",
            "jean.dupont@example.com": "EMAIL_TOKEN_1",
            "Paris": "LOC_TOKEN_1",
            "Beta Services": "ORG_TOKEN_1",
        },
    )

    processor.reconstruct_and_write_anonymized_file(
        output_path, final_blocks, input_path
    )

    actual_blocks = [
        block for block in DocxProcessor().extract_blocks(output_path) if block.strip()
    ]
    assert actual_blocks == [
        "Contrat de PER_TOKEN_1",
        "Email",
        "EMAIL_TOKEN_1",
        "Ville",
        "LOC_TOKEN_1",
        "Confidentiel PER_TOKEN_2",
        "Archive ORG_TOKEN_1",
    ]
    _assert_no_sensitive_text("\n".join(actual_blocks))


def test_xlsx_golden_snapshot_multisheet(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from anonyfiles_core.anonymizer.excel_processor import ExcelProcessor

    input_path = tmp_path / "sample.xlsx"
    output_path = tmp_path / "sample_anonymized.xlsx"

    workbook = openpyxl.Workbook()
    contacts = workbook.active
    contacts.title = "Contacts"
    contacts.append(["Nom", "Email", "Ville"])
    contacts.append(["Jean Dupont", "jean.dupont@example.com", "Paris"])
    audit = workbook.create_sheet("Audit")
    audit.append(["Organisation", "IBAN"])
    audit.append(["Beta Services", "FR76 3000 6000 0112 3456 7890 189"])
    workbook.save(input_path)

    processor = ExcelProcessor()
    blocks = processor.extract_blocks(input_path)
    final_blocks = _replace_blocks(
        blocks,
        {
            "Jean Dupont": "PER_TOKEN_1",
            "jean.dupont@example.com": "EMAIL_TOKEN_1",
            "Paris": "LOC_TOKEN_1",
            "Beta Services": "ORG_TOKEN_1",
            "FR76 3000 6000 0112 3456 7890 189": "IBAN_TOKEN_1",
        },
    )

    processor.reconstruct_and_write_anonymized_file(
        output_path, final_blocks, input_path
    )

    actual_workbook = openpyxl.load_workbook(output_path)
    assert actual_workbook.sheetnames == ["Contacts", "Audit"]
    assert _sheet_values(actual_workbook["Contacts"]) == [
        ["Nom", "Email", "Ville"],
        ["PER_TOKEN_1", "EMAIL_TOKEN_1", "LOC_TOKEN_1"],
    ]
    assert _sheet_values(actual_workbook["Audit"]) == [
        ["Organisation", "IBAN"],
        ["ORG_TOKEN_1", "IBAN_TOKEN_1"],
    ]
    _assert_no_sensitive_text(_workbook_text(actual_workbook))


def test_pdf_golden_snapshot_extractable_text(tmp_path):
    fitz = pytest.importorskip("fitz")
    PdfReader = pytest.importorskip("pypdf").PdfReader

    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "sample_anonymized.pdf"
    _write_simple_pdf(
        input_path,
        [
            ["Contrat PDF: Jean Dupont", "Email: jean.dupont@example.com"],
            ["Societe: Beta Services", "Ville: Paris"],
        ],
    )

    replacement_map = {
        "Jean Dupont": "PER_1",
        "jean.dupont@example.com": "MAIL_1",
        "Beta Services": "ORG_1",
        "Paris": "LOC_1",
    }
    processor = PdfProcessor()
    processor.reconstruct_and_write_anonymized_file(
        output_path,
        ["Contrat PDF: PER_1\nEmail: MAIL_1", "Societe: ORG_1\nVille: LOC_1"],
        input_path,
        spacy_replacements_map=replacement_map,
    )

    result_doc = fitz.open(output_path)
    pymupdf_text = "\n".join(page.get_text("text") for page in result_doc)
    pypdf_text = "\n".join(
        page.extract_text() or "" for page in PdfReader(output_path).pages
    )
    combined_text = f"{pymupdf_text}\n{pypdf_text}"

    assert len(result_doc) == 2
    for token in replacement_map.values():
        assert token in combined_text
    _assert_no_sensitive_text(combined_text)


def _sheet_values(sheet):
    return [[cell.value for cell in row] for row in sheet.iter_rows()]


def _workbook_text(workbook):
    values = []
    for sheet_name in workbook.sheetnames:
        for row in _sheet_values(workbook[sheet_name]):
            values.extend("" if value is None else str(value) for value in row)
    return "\n".join(values)


def _write_simple_pdf(path: Path, pages):
    canvas_module = pytest.importorskip("reportlab.pdfgen.canvas")
    canvas = canvas_module.Canvas(str(path))
    for lines in pages:
        y = 760
        for line in lines:
            canvas.drawString(72, y, line)
            y -= 24
        canvas.showPage()
    canvas.save()
