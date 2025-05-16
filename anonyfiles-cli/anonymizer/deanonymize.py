# anonymizer/deanonymize.py

import csv
from collections import defaultdict
from typing import Dict, Set, Tuple, List, Optional

class Deanonymizer:
    def __init__(self, mapping_path: str, strict: bool = True):
        self.mapping_path = mapping_path
        self.strict = strict
        self.code_to_originals: Dict[str, Set[str]] = defaultdict(set)
        self.warnings: List[str] = []
        self.collisions: Dict[str, Set[str]] = {}
        self.unknown_codes: Set[str] = set()
        self.load_mapping()

    def load_mapping(self):
        """
        Charge le mapping CSV et détecte les collisions de mapping.
        Compatible avec en-tête 'Code,Nom Original' OU 'anonymized,original'.
        """
        with open(self.mapping_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            # Détecte le nom des colonnes à utiliser
            possible_code_fields = ["anonymized", "Code"]
            possible_original_fields = ["original", "Nom Original"]

            # Vérifie que le header contient bien au moins un des deux
            header_fields = reader.fieldnames or []
            code_field = next((f for f in possible_code_fields if f in header_fields), None)
            original_field = next((f for f in possible_original_fields if f in header_fields), None)

            if not code_field or not original_field:
                raise KeyError(
                    f"Impossible de trouver les colonnes 'anonymized/original' ou 'Code/Nom Original' dans le mapping. "
                    f"Colonnes trouvées : {header_fields}"
                )

            for row in reader:
                anonymized = row[code_field]
                original = row[original_field]
                self.code_to_originals[anonymized].add(original)

        # Détecte les collisions
        for code, originals in self.code_to_originals.items():
            if len(originals) > 1:
                self.collisions[code] = originals
                self.warnings.append(
                    f"Collision : le code {code} correspond à plusieurs originaux : {list(originals)}"
                )

    def deanonymize_text(self, text: str, dry_run: bool = False) -> Tuple[str, dict]:
        """
        Restaure le texte anonymisé, gère les collisions et codes inconnus.
        Retourne le texte restauré et un rapport détaillé.
        """
        import re

        replaced = 0
        code_pattern = re.compile(r'\b([A-Z]+\d{3,}|\[REDACTED[^\]]*\])\b')
        all_codes_in_text = set(re.findall(code_pattern, text))
        codes_found = set()
        codes_ambiguous = set()

        def replacement(match):
            code = match.group(0)
            if code in self.code_to_originals:
                originals = self.code_to_originals[code]
                codes_found.add(code)
                if len(originals) == 1:
                    return next(iter(originals))
                else:
                    codes_ambiguous.add(code)
                    if dry_run or not self.strict:
                        return f"[AMBIGUOUS_{code}]"
                    else:
                        self.warnings.append(
                            f"Collision non résolue pour {code} dans le texte"
                        )
                        return f"[AMBIGUOUS_{code}]"
            else:
                self.unknown_codes.add(code)
                if dry_run or not self.strict:
                    return f"[UNKNOWN_MAPPING:{code}]"
                else:
                    self.warnings.append(f"Code inconnu : {code}")
                    return f"[UNKNOWN_MAPPING:{code}]"

        # Effectue le remplacement
        result = re.sub(code_pattern, replacement, text)
        replaced = len(codes_found) + len(codes_ambiguous)

        # Récap du rapport
        report = {
            "codes_in_text": all_codes_in_text,
            "codes_found": codes_found,
            "codes_ambiguous": codes_ambiguous,
            "codes_not_found": self.unknown_codes,
            "collisions": self.collisions,
            "warnings": self.warnings,
            "replaced_count": replaced,
            "coverage": f"{(len(codes_found)/len(all_codes_in_text)*100):.1f}%" if all_codes_in_text else "0%",
            "dry_run": dry_run,
            "strict": self.strict
        }
        return result, report

    def generate_report(self, report: dict, output_path: Optional[str] = None):
        """
        Génère un rapport lisible (stdout ou fichier)
        """
        lines = []
        lines.append("=== Rapport de désanonymisation ===")
        lines.append(f"Mode dry-run: {report['dry_run']}")
        lines.append(f"Mode strict: {report['strict']}")
        lines.append(f"Nombre total de codes trouvés dans le texte : {len(report['codes_in_text'])}")
        lines.append(f"Nombre de codes remplacés (uniques) : {len(report['codes_found'])}")
        lines.append(f"Collisions détectées : {len(report['codes_ambiguous'])}")
        lines.append(f"Codes non trouvés dans mapping : {len(report['codes_not_found'])}")
        lines.append(f"Couverture du mapping : {report['coverage']}")
        if report['collisions']:
            lines.append("---- Collisions ----")
            for code, originals in report['collisions'].items():
                lines.append(f"  - {code} : {list(originals)}")
        if report['codes_not_found']:
            lines.append("---- Codes inconnus dans le texte ----")
            for code in report['codes_not_found']:
                lines.append(f"  - {code}")
        if report['warnings']:
            lines.append("---- Avertissements ----")
            for w in report['warnings']:
                lines.append(f"  - {w}")

        result = "\n".join(lines)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            print(result)

# Exemple d'utilisation :
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python deanonymize.py <input_file> <mapping_csv> <output_file> [--dry-run] [--strict/--permissive]")
        sys.exit(1)
    input_file = sys.argv[1]
    mapping_csv = sys.argv[2]
    output_file = sys.argv[3]
    dry_run = "--dry-run" in sys.argv
    strict = "--permissive" not in sys.argv  # strict par défaut

    deanonymizer = Deanonymizer(mapping_csv, strict=strict)
    with open(input_file, encoding="utf-8") as f:
        content = f.read()
    result, report = deanonymizer.deanonymize_text(content, dry_run=dry_run)
    if not dry_run:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
    deanonymizer.generate_report(report)
