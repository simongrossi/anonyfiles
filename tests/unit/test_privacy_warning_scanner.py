from anonyfiles_core.anonymizer.privacy_warning_scanner import (
    privacy_warning_count,
    scan_blocks_for_privacy_warnings,
)


def test_scanner_reports_suspicious_values_by_category():
    warnings = scan_blocks_for_privacy_warnings(
        [
            "Pierre contacte ambre [at] exemple [dot] fr.\n"
            "Tel: +33 (0)6 12 34 56 78\n"
            "Adresse: 12 rue Victor Hugo 75015 Paris\n"
            "KMCL\n"
        ],
        enabled_labels={"PER", "EMAIL", "PHONE", "ADDRESS", "ORG", "MISC"},
    )

    by_kind = {warning["kind"]: warning for warning in warnings}
    assert by_kind["EMAIL"]["count"] == 1
    assert by_kind["PHONE"]["count"] == 1
    assert by_kind["ADDRESS"]["count"] == 1
    assert by_kind["FIRST_NAME"]["count"] >= 1
    assert by_kind["UPPERCASE_TOKEN"]["examples"] == ["KMCL"]
    assert privacy_warning_count(warnings) >= 5


def test_scanner_ignores_generated_placeholders_and_replacements():
    warnings = scan_blocks_for_privacy_warnings(
        ["{{NOM_001}} [ENTREPRISE_ANONYME_1] Jean Martin " "contact@example.com"],
        enabled_labels={"PER", "EMAIL", "ORG", "MISC"},
        ignored_values={"Jean Martin", "contact@example.com"},
    )

    assert warnings == []


def test_scanner_respects_disabled_labels():
    warnings = scan_blocks_for_privacy_warnings(
        ["Pierre contacte ambre [at] exemple [dot] fr.\nKMCL\n"],
        enabled_labels={"EMAIL"},
    )

    by_kind = {warning["kind"]: warning for warning in warnings}
    assert set(by_kind) == {"EMAIL"}
