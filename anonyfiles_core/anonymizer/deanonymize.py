# /home/debian/anonyfiles/anonyfiles_cli/anonymizer/deanonymize.py

import csv
from collections import defaultdict
from typing import Dict, Set, Tuple, List, Optional
import re
from .format_utils import ANY_PLACEHOLDER_REGEX, parse_placeholder

class Deanonymizer:
    def __init__(self, mapping_path: str, strict: bool = True):
        self.mapping_path = mapping_path
        self.strict = strict
        self.code_to_originals: Dict[str, Set[str]] = defaultdict(set)
        self.warnings: List[str] = []
        self.map_loading_warnings: List[str] = []
        self.collisions: Dict[str, Set[str]] = {}
        self.unknown_codes_in_text: Set[str] = set()
        self._load_mapping()

    def _load_mapping(self):
        try:
            with open(self.mapping_path, newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                possible_code_fields = ["anonymized", "Code"]
                possible_original_fields = ["original", "Nom Original"]
                possible_label_fields = ["label", "Label"] # Nouveau : pour le label
                possible_source_fields = ["source", "Source"] # Nouveau : pour la source
                header_fields = reader.fieldnames
                if not header_fields:
                    self.map_loading_warnings.append(f"Fichier mapping vide ou sans en-tête : {self.mapping_path}")
                    return

                code_field = next((f for f in possible_code_fields if f in header_fields), None)
                original_field = next((f for f in possible_original_fields if f in header_fields), None)
                label_field = next((f for f in possible_label_fields if f in header_fields), None)
                source_field = next((f for f in possible_source_fields if f in header_fields), None)


                if not code_field or not original_field:
                    self.map_loading_warnings.append(
                        f"Colonnes requises ('anonymized'/'Code' ET 'original'/'Nom Original') non trouvées "
                        f"dans {self.mapping_path}. Colonnes trouvées : {header_fields}"
                    )
                    return

                for row_number, row in enumerate(reader, 1):
                    try:
                        anonymized_val = row.get(code_field)
                        original_val = row.get(original_field)
                        # Pour l'instant, on ne stocke pas label ou source directement dans code_to_originals
                        # car il n'est pas utilisé pour la logique de remplacement.
                        # Il serait pertinent si on voulait filtrer par label ou source pendant la désanonymisation.
                        # Mais pour la désanonymisation simple, code -> original suffit.
                        # Cependant, pour le rapport, on pourrait les récupérer si nécessaire.

                        if anonymized_val is not None and original_val is not None:
                            self.code_to_originals[anonymized_val.strip()].add(original_val.strip())
                        else:
                            self.map_loading_warnings.append(
                                f"Ligne {row_number} ignorée dans {self.mapping_path}: valeur de code ou d'original manquante/None."
                            )
                    except Exception as e_row:
                        self.map_loading_warnings.append(
                             f"Erreur à la ligne {row_number} dans {self.mapping_path}: {str(e_row)}."
                        )

            temp_collisions = {}
            for code, originals in self.code_to_originals.items():
                if len(originals) > 1:
                    temp_collisions[code] = originals
                    self.map_loading_warnings.append(
                        f"Collision dans le mapping: le code '{code}' correspond à plusieurs originaux : {list(originals)}"
                    )
            self.collisions = temp_collisions

        except FileNotFoundError:
            self.map_loading_warnings.append(f"Fichier mapping non trouvé : {self.mapping_path}")
        except Exception as e:
            self.map_loading_warnings.append(f"Erreur majeure lors du chargement du fichier mapping {self.mapping_path}: {str(e)}")

    def deanonymize_text(self, text: str, dry_run: bool = False) -> Tuple[str, dict]:
        self.warnings = list(self.map_loading_warnings)
        self.unknown_codes_in_text = set()

        # Motif pour repérer les codes anonymisés (ex: {{NOM_XXX}} ou [CUSTOM_REDACTED])
        # Centralisé dans ``format_utils`` pour éviter la duplication.
        code_pattern = ANY_PLACEHOLDER_REGEX

        all_distinct_codes_found_in_text = set()
        attempted_replacements_info = {"successful": 0, "ambiguous_kept": 0, "unknown_kept": 0}

        def replacement_function(match_obj):
            code_from_text = match_obj.group(0)
            parse_placeholder(code_from_text)  # Validate format centrally
            all_distinct_codes_found_in_text.add(code_from_text)

            if code_from_text in self.code_to_originals:
                originals_set = self.code_to_originals[code_from_text]

                if len(originals_set) == 1:
                    attempted_replacements_info["successful"] += 1
                    return next(iter(originals_set))
                else:
                    attempted_replacements_info["ambiguous_kept"] += 1
                    warning_msg = f"Collision: Le code '{code_from_text}' dans le texte correspond à plusieurs originaux ({list(originals_set)}). Placeholder inséré."
                    if warning_msg not in self.warnings: self.warnings.append(warning_msg)
                    return f"[AMBIGUOUS_CODE:{code_from_text}]"

            else:
                self.unknown_codes_in_text.add(code_from_text)
                attempted_replacements_info["unknown_kept"] += 1
                warning_msg = f"Code inconnu: Le code '{code_from_text}' trouvé dans le texte n'a pas de correspondance dans le mapping. Placeholder inséré."
                if warning_msg not in self.warnings: self.warnings.append(warning_msg)
                return f"[UNKNOWN_MAPPING:{code_from_text}]"

        result_text = text
        if self.code_to_originals or not self.map_loading_warnings:
            result_text = re.sub(code_pattern, replacement_function, text)
        else:
            self.warnings.append("Désanonymisation ignorée car le mapping n'a pas pu être chargé ou est vide.")

        codes_in_mapping_that_were_referenced = {k for k in self.code_to_originals if k in all_distinct_codes_found_in_text}

        report = {
            "distinct_codes_in_text_list": sorted(list(all_distinct_codes_found_in_text)),
            "distinct_codes_in_text_count": len(all_distinct_codes_found_in_text),
            "codes_from_text_found_in_mapping_count": len(codes_in_mapping_that_were_referenced),
            "codes_from_text_not_found_in_mapping_list": sorted(list(self.unknown_codes_in_text)),
            "codes_from_text_not_found_in_mapping_count": len(self.unknown_codes_in_text),
            "map_collisions_details": self.collisions,
            "warnings_generated_during_deanonymization": self.warnings,
            "replacements_successful_count": attempted_replacements_info["successful"],
            "replacements_ambiguous_kept_count": attempted_replacements_info["ambiguous_kept"],
            "replacements_unknown_kept_count": attempted_replacements_info["unknown_kept"],
            "coverage_percentage": f"{(len(codes_in_mapping_that_were_referenced) / len(all_distinct_codes_found_in_text) * 100):.1f}%" if all_distinct_codes_found_in_text else "0%",
            "dry_run": dry_run,
            "strict_mode": self.strict
        }
        return result_text, report

    def generate_report(self, report: dict, output_path: Optional[str] = None):
        lines = [
            "=== Rapport de Désanonymisation ===",
            f"Mode dry-run: {report['dry_run']}",
            f"Mode strict: {report['strict_mode']}",
            f"Codes uniques (placeholders/anonymes) détectés dans le texte source: {report['distinct_codes_in_text_count']}",
            f"  - D'entre eux, trouvés dans le fichier mapping: {report['codes_from_text_found_in_mapping_count']}",
            f"  - D'entre eux, NON trouvés dans le fichier mapping: {report['codes_from_text_not_found_in_mapping_count']}",
            f"Remplacements effectifs (par valeur originale unique): {report['replacements_successful_count']}",
            f"Codes ambigus (multiples originaux possibles, marqués {report['replacements_ambiguous_kept_count']} fois)",
            f"Codes inconnus (non mappés, marqués {report['replacements_unknown_kept_count']} fois)",
            f"Couverture du mapping (codes du texte présents dans mapping): {report['coverage_percentage']}",
        ]

        map_collisions_display = report.get('map_collisions_details', {})
        if map_collisions_display:
            lines.append("\n---- Collisions détectées dans le fichier mapping (code -> multiples originaux) ----")
            for code, originals_set in map_collisions_display.items():
                lines.append(f"  - Code '{code}' peut correspondre à : {list(originals_set)}")
        
        if report.get('codes_from_text_not_found_in_mapping_list'):
            lines.append("\n---- Codes du texte source NON TROUVÉS dans le fichier mapping ----")
            for code in report['codes_from_text_not_found_in_mapping_list']:
                lines.append(f"  - '{code}'")
        
        if report.get('warnings_generated_during_deanonymization'):
            lines.append("\n---- Avertissements générés (chargement mapping inclus) ----")
            for idx, warning_msg in enumerate(report['warnings_generated_during_deanonymization']):
                lines.append(f"  - {idx+1}: {warning_msg}")

        final_report_text = "\n".join(lines)
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f_report:
                    f_report.write(final_report_text)
                print(f"\nRapport de désanonymisation sauvegardé dans : {output_path}")
            except Exception as e:
                print(f"\nErreur lors de la sauvegarde du rapport: {e}")
                print("\n--- Contenu du Rapport ---")
                print(final_report_text)
                print("--- Fin du Contenu du Rapport ---")
        else:
            print("\n" + final_report_text)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python deanonymize.py <input_file_path> <mapping_csv_path> <output_file_path> [--dry-run] [--strict | --permissive]")
        sys.exit(1)
    
    cli_input_file_path = sys.argv[1]
    cli_mapping_csv_path = sys.argv[2]
    cli_output_file_path = sys.argv[3]
    
    cli_is_dry_run_mode = "--dry-run" in sys.argv
    
    cli_is_strict_mode_active = True
    if "--permissive" in sys.argv:
        cli_is_strict_mode_active = False
    
    print(f"Lancement désanonymisation via CLI: Entrée='{cli_input_file_path}', Mapping='{cli_mapping_csv_path}', Sortie='{cli_output_file_path}'")
    print(f"Options: dry-run={cli_is_dry_run_mode}, strict={cli_is_strict_mode_active}")

    try:
        cli_deanonymizer_instance = Deanonymizer(cli_mapping_csv_path, strict=cli_is_strict_mode_active)
        
        if cli_deanonymizer_instance.map_loading_warnings and not cli_deanonymizer_instance.code_to_originals:
            print("\nERREUR CRITIQUE: Le fichier de mapping n'a pas pu être chargé correctement ou est vide. Voir avertissements:")
            minimal_report_for_error = {
                "dry_run": cli_is_dry_run_mode,
                "strict_mode": cli_is_strict_mode_active,
                "warnings_generated_during_deanonymization": cli_deanonymizer_instance.map_loading_warnings,
                "map_collisions_details": cli_deanonymizer_instance.collisions,
                "distinct_codes_in_text_count": 0,
                "codes_from_text_found_in_mapping_count": 0,
                "codes_from_text_not_found_in_mapping_count": 0,
                "replacements_successful_count": 0,
                "replacements_ambiguous_kept_count": 0,
                "replacements_unknown_kept_count": 0,
                "coverage_percentage": "N/A",
                "codes_from_text_not_found_in_mapping_list": []
            }
            cli_deanonymizer_instance.generate_report(minimal_report_for_error)
            sys.exit(1)

        with open(cli_input_file_path, "r", encoding="utf-8") as f_input_cli:
            cli_source_text_content = f_input_cli.read()
        
        cli_restored_text_content, cli_report_information = cli_deanonymizer_instance.deanonymize_text(cli_source_text_content, dry_run=cli_is_dry_run_mode)
        
        if not cli_is_dry_run_mode:
            with open(cli_output_file_path, "w", encoding="utf-8") as f_output_cli:
                f_output_cli.write(cli_restored_text_content)
            print(f"\nTexte désanonymisé écrit dans : {cli_output_file_path}")
        
        cli_deanonymizer_instance.generate_report(cli_report_information)

        if cli_is_dry_run_mode:
            print("\nNOTE: C'était un dry-run. Aucun fichier de sortie n'a été modifié ou créé.")

    except FileNotFoundError as e_fnf_cli:
        print(f"Erreur (CLI): Fichier non trouvé - {e_fnf_cli}")
    except KeyError as e_key_cli:
        print(f"Erreur (CLI): Problème avec les colonnes du fichier mapping - {e_key_cli}")
    except Exception as e_main_cli:
        print(f"Une erreur inattendue est survenue (CLI): {e_main_cli}")
        import traceback
        traceback.print_exc()
