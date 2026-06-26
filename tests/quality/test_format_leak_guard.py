import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("spacy")

from anonyfiles_cli.exceptions import ConfigurationError
from anonyfiles_core import AnonyfilesEngine

P0_FORMAT_CONFIG = {
    "spacy_model": "fr_core_news_md",
    "anonymizeLocations": False,
    "anonymizeOrgs": False,
    "anonymizeMisc": False,
    "replacements": {
        "PER": {"type": "redact", "options": {"text": "PER_TOKEN"}},
        "DATE": {"type": "redact", "options": {"text": "DATE_TOKEN"}},
        "EMAIL": {"type": "redact", "options": {"text": "EMAIL_TOKEN"}},
        "PHONE": {"type": "redact", "options": {"text": "PHONE_TOKEN"}},
        "IBAN": {"type": "redact", "options": {"text": "IBAN_TOKEN"}},
        "ADDRESS": {"type": "redact", "options": {"text": "ADDRESS_TOKEN"}},
    },
}


def _engine() -> AnonyfilesEngine:
    try:
        return AnonyfilesEngine(config=P0_FORMAT_CONFIG)
    except ConfigurationError as exc:
        pytest.skip(f"Modele spaCy indisponible pour les tests P0 formats: {exc}")


def _run_anonymization(input_path: Path, output_path: Path, **kwargs):
    result = _engine().anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        mapping_output_path=input_path.with_suffix(".mapping.csv"),
        log_entities_path=input_path.with_suffix(".entities.csv"),
        **kwargs,
    )
    assert result["status"] == "success", result.get("error")
    assert output_path.exists()
    return result


def _assert_no_leaks(rendered_output: str, sensitive_values: list[str]):
    folded_output = rendered_output.casefold()
    for value in sensitive_values:
        assert (
            value.casefold() not in folded_output
        ), f"Sensitive value leaked in final output: {value!r}"


def _assert_detected_labels(result, expected_labels: set[str]):
    detected_labels = {label for _text, label in result["entities_detected"]}
    assert expected_labels.issubset(detected_labels)


def _docx_text(path: Path) -> str:
    pytest.importorskip("docx")
    from anonyfiles_core.anonymizer.word_processor import DocxProcessor

    return "\n".join(DocxProcessor().extract_blocks(path))


def _xlsx_text(path: Path) -> str:
    openpyxl = pytest.importorskip("openpyxl")

    workbook = openpyxl.load_workbook(path, data_only=False)
    values: list[str] = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows(values_only=True):
            for value in row:
                if value is not None:
                    values.append(str(value))
    return "\n".join(values)


def _pdf_text(path: Path) -> str:
    fitz = pytest.importorskip("fitz")
    PdfReader = pytest.importorskip("pypdf").PdfReader

    doc = fitz.open(path)
    try:
        pymupdf_text = "\n".join(page.get_text("text") for page in doc)
    finally:
        doc.close()
    pypdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return f"{pymupdf_text}\n{pypdf_text}"


def _write_simple_pdf(path: Path, pages: list[list[str]]):
    canvas_module = pytest.importorskip("reportlab.pdfgen.canvas")
    canvas = canvas_module.Canvas(str(path))
    for lines in pages:
        y = 760
        for line in lines:
            canvas.drawString(72, y, line)
            y -= 24
        canvas.showPage()
    canvas.save()


def test_txt_p0_leak_guard_final_file(tmp_path):
    input_path = tmp_path / "note.txt"
    output_path = tmp_path / "note_anonymized.txt"
    sensitive_values = [
        "Simon Grossi",
        "simon.grossi@example.com",
        "06 12 34 56 78",
        "4 avenue de la Republique, 69002 Lyon",
        "FR76 3000 6000 0112 3456 7890 189",
        "Pierre",
        "Ambre",
    ]
    input_path.write_text(
        "Compte rendu confidentiel.\n"
        "Client: Simon Grossi\n"
        "Email: simon.grossi@example.com\n"
        "Téléphone: 06 12 34 56 78\n"
        "Adresse: 4 avenue de la Republique, 69002 Lyon.\n"
        "IBAN: FR76 3000 6000 0112 3456 7890 189\n"
        "Participants:\nPierre\nAmbre\n"
        "Références publiques: KMCL, Alencon, EMAIL-2026.\n",
        encoding="utf-8",
    )

    result = _run_anonymization(input_path, output_path)

    rendered_output = output_path.read_text(encoding="utf-8")

    _assert_no_leaks(rendered_output, sensitive_values)
    assert "KMCL" in rendered_output
    assert "Alencon" in rendered_output
    assert "EMAIL-2026" in rendered_output
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS", "IBAN"})


def test_csv_p0_leak_guard_with_header(tmp_path):
    input_path = tmp_path / "contacts.csv"
    output_path = tmp_path / "contacts_anonymized.csv"
    sensitive_values = [
        "Élise Martin",
        "elise.martin+rh@example.org",
        "+33 6 11 22 33 44",
        "12 Rue Victor-Hugo, 75015 Paris",
        "Ambre Lenoir",
        "ambre.lenoir@example.com",
        "06.11.22.33.44",
        "7 allée des Érables, 31000 Toulouse",
    ]

    with input_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["name", "email", "phone", "address", "note"])
        writer.writerow(
            [
                "Élise Martin",
                "elise.martin+rh@example.org",
                "+33 6 11 22 33 44",
                "12 Rue Victor-Hugo, 75015 Paris",
                "Référence non sensible: SIREN-2026 et Parisien",
            ]
        )
        writer.writerow(
            [
                "Ambre Lenoir",
                "ambre.lenoir@example.com",
                "06.11.22.33.44",
                "7 allée des Érables, 31000 Toulouse",
                "Conserver: dossier-4821",
            ]
        )

    result = _run_anonymization(input_path, output_path, has_header=True)

    with output_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file))
    rendered_output = json.dumps(rows, ensure_ascii=False)

    _assert_no_leaks(rendered_output, sensitive_values)
    assert len(rows) == 3
    assert rows[0] == ["name", "email", "phone", "address", "note"]
    assert "SIREN-2026" in rendered_output
    assert "Parisien" in rendered_output
    assert "dossier-4821" in rendered_output
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS"})


def test_json_p0_leak_guard_nested_values(tmp_path):
    input_path = tmp_path / "payload.json"
    output_path = tmp_path / "payload_anonymized.json"
    sensitive_values = [
        "Simon Grossi",
        "simon.grossi@example.com",
        "06 12 34 56 78",
        "4 avenue de la Republique, 69002 Lyon",
        "FR76 3000 6000 0112 3456 7890 189",
        "Pierre",
        "Ambre",
    ]
    payload = {
        "customer": {
            "name": "Simon Grossi",
            "contact": {
                "email": "simon.grossi@example.com",
                "phone": "06 12 34 56 78",
            },
            "address": "4 avenue de la Republique, 69002 Lyon",
        },
        "payment": {
            "iban": "FR76 3000 6000 0112 3456 7890 189",
            "reference": "IBAN-2026",
        },
        "attendees": ["Pierre", "Ambre"],
        "public_tags": ["KMCL", "Alencon", "EMAIL-2026"],
    }
    input_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    result = _run_anonymization(input_path, output_path)

    output_payload = json.loads(output_path.read_text(encoding="utf-8"))
    rendered_output = json.dumps(output_payload, ensure_ascii=False)

    _assert_no_leaks(rendered_output, sensitive_values)
    assert output_payload["payment"]["reference"] == "IBAN-2026"
    assert output_payload["public_tags"] == ["KMCL", "Alencon", "EMAIL-2026"]
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS", "IBAN"})


def test_docx_p0_leak_guard_body_table_header_footer(tmp_path):
    Document = pytest.importorskip("docx").Document

    input_path = tmp_path / "contract.docx"
    output_path = tmp_path / "contract_anonymized.docx"
    sensitive_values = [
        "Élise Martin",
        "elise.martin+rh@example.org",
        "+33 6 11 22 33 44",
        "12 Rue Victor-Hugo, 75015 Paris",
        "Ambre Lenoir",
        "ambre.lenoir@example.com",
        "FR76 3000 6000 0112 3456 7890 189",
    ]

    doc = Document()
    doc.add_paragraph("Contrat de prestation pour Élise Martin")
    doc.add_paragraph("Adresse personnelle: 12 Rue Victor-Hugo, 75015 Paris.")
    table = doc.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "Email"
    table.cell(0, 1).text = "elise.martin+rh@example.org"
    table.cell(1, 0).text = "Téléphone"
    table.cell(1, 1).text = "+33 6 11 22 33 44"
    table.cell(2, 0).text = "Référence"
    table.cell(2, 1).text = "SIREN-2026"
    section = doc.sections[0]
    section.header.paragraphs[0].text = "Confidentiel Ambre Lenoir"
    section.footer.paragraphs[0].text = "IBAN: FR76 3000 6000 0112 3456 7890 189"
    doc.save(input_path)

    result = _run_anonymization(input_path, output_path)

    rendered_output = _docx_text(output_path)

    _assert_no_leaks(rendered_output, sensitive_values)
    assert "SIREN-2026" in rendered_output
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS", "IBAN"})


def test_xlsx_p0_leak_guard_all_sheets(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")

    input_path = tmp_path / "workbook.xlsx"
    output_path = tmp_path / "workbook_anonymized.xlsx"
    sensitive_values = [
        "Simon Grossi",
        "simon.grossi@example.com",
        "06 12 34 56 78",
        "4 avenue de la Republique, 69002 Lyon",
        "FR76 3000 6000 0112 3456 7890 189",
        "Pierre",
        "Ambre",
    ]

    workbook = openpyxl.Workbook()
    contacts = workbook.active
    contacts.title = "Contacts"
    contacts.append(["Nom", "Email", "Téléphone", "Adresse"])
    contacts.append(
        [
            "Simon Grossi",
            "simon.grossi@example.com",
            "06 12 34 56 78",
            "4 avenue de la Republique, 69002 Lyon",
        ]
    )
    payments = workbook.create_sheet("Paiements")
    payments.append(["IBAN", "Référence"])
    payments.append(["FR76 3000 6000 0112 3456 7890 189", "IBAN-2026"])
    attendees = workbook.create_sheet("Participants")
    attendees.append(["Prénom", "Note"])
    attendees.append(["Pierre", "KMCL"])
    attendees.append(["Ambre", "Alencon"])
    workbook.save(input_path)

    result = _run_anonymization(input_path, output_path)

    rendered_output = _xlsx_text(output_path)

    _assert_no_leaks(rendered_output, sensitive_values)
    assert "IBAN-2026" in rendered_output
    assert "KMCL" in rendered_output
    assert "Alencon" in rendered_output
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS", "IBAN"})


def test_pdf_p0_leak_guard_extractable_text(tmp_path):
    input_path = tmp_path / "contract.pdf"
    output_path = tmp_path / "contract_anonymized.pdf"
    sensitive_values = [
        "Simon Grossi",
        "simon.grossi@example.com",
        "06 12 34 56 78",
        "4 avenue de la Republique, 69002 Lyon",
        "FR76 3000 6000 0112 3456 7890 189",
        "Pierre",
        "Ambre",
    ]
    _write_simple_pdf(
        input_path,
        [
            [
                "Contrat PDF confidentiel",
                "Client: Simon Grossi",
                "Email: simon.grossi@example.com",
                "Telephone: 06 12 34 56 78",
                "Adresse: 4 avenue de la Republique, 69002 Lyon.",
                "IBAN: FR76 3000 6000 0112 3456 7890 189",
            ],
            [
                "Participants:",
                "Pierre",
                "Ambre",
                "References publiques: KMCL, Alencon, EMAIL-2026.",
            ],
        ],
    )

    result = _run_anonymization(input_path, output_path)

    rendered_output = _pdf_text(output_path)

    _assert_no_leaks(rendered_output, sensitive_values)
    assert "KMCL" in rendered_output
    assert "Alencon" in rendered_output
    assert "EMAIL-2026" in rendered_output
    _assert_detected_labels(result, {"PER", "EMAIL", "PHONE", "ADDRESS", "IBAN"})
