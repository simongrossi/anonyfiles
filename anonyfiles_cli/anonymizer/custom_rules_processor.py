# anonyfiles_cli/anonymizer/custom_rules_processor.py

import re
from typing import List, Dict, Any, Optional
import typer

from .audit import AuditLogger

class CustomRulesProcessor:
    """
    Gère l'application des règles de remplacement personnalisées sur des blocs de texte.
    """
    def __init__(self, custom_replacement_rules: Optional[List[Dict[str, Any]]], audit_logger: AuditLogger):
        self.custom_rules: List[Dict[str, Any]] = []
        self.audit_logger = audit_logger
        self.custom_replacements_mapping: Dict[str, str] = {}
        self.custom_replacements_count = 0
        if custom_replacement_rules:
            for rule in custom_replacement_rules:
                # Ignore empty patterns early
                pattern_str = rule.get("pattern")
                if not pattern_str:
                    continue

                if rule.get("isRegex", False):
                    try:
                        rule["compiled_pattern"] = re.compile(pattern_str, flags=re.IGNORECASE)
                    except re.error as e:
                        typer.echo(
                            f"AVERTISSEMENT (CustomRulesProcessor): Regex invalide pour la règle personnalisée '{pattern_str}': {e}. Règle ignorée.",
                            err=True,
                        )
                        continue

                self.custom_rules.append(rule)

        if self.custom_rules:
            typer.echo(
                f"DEBUG (CustomRulesProcessor Init): Initialisé avec {len(self.custom_rules)} règle(s) personnalisée(s)."
            )

    def apply_to_block(self, text_block: str) -> str:
        """
        Applique les règles personnalisées à un bloc de texte donné.
        Met à jour le journal d'audit et le mapping des règles personnalisées.
        """
        if not self.custom_rules:
            return text_block

        modified_text = text_block
        for rule in self.custom_rules:
            pattern_str = rule.get("pattern")
            replacement = rule.get("replacement", "[CUSTOM_REDACTED]")
            is_regex = rule.get("isRegex", False)
            compiled_pattern: Optional[re.Pattern] = rule.get("compiled_pattern")
            
            if not pattern_str:
                continue

            try:
                if is_regex and compiled_pattern is not None:
                    # Capture all occurrences to log each replacement
                    # Utilise une copie temporaire pour itérer afin d'éviter les problèmes
                    # si `modified_text` est altéré pendant l'itération.
                    temp_modified_text_for_re_finditer = modified_text 
                    for match in compiled_pattern.finditer(temp_modified_text_for_re_finditer):
                        matched_text = re.escape(match.group(0)) # Escape pour le sub pour ne pas interpréter comme regex
                        
                        # Remplacer une occurrence à la fois pour ne pas créer de chevauchements
                        # qui seraient complexes à tracer.
                        modified_text, num_replacements_made = re.subn(matched_text, replacement, modified_text, 1)
                        if num_replacements_made > 0:
                            self.audit_logger.log(matched_text, replacement, "custom_regex", 1, original_text=match.group(0))
                            self.custom_replacements_count += 1
                            self.custom_replacements_mapping[match.group(0)] = replacement
                else:
                    # Simple text replacement
                    count = modified_text.count(pattern_str)
                    if count > 0:
                        modified_text = modified_text.replace(pattern_str, replacement)
                        self.audit_logger.log(pattern_str, replacement, "custom_text", count, original_text=pattern_str)
                        self.custom_replacements_count += count
                        self.custom_replacements_mapping[pattern_str] = replacement
            except re.error as e:
                typer.echo(f"AVERTISSEMENT (CustomRulesProcessor): Regex invalide pour la règle personnalisée '{pattern_str}': {e}. Règle ignorée.", err=True)
        return modified_text

    def get_custom_replacements_mapping(self) -> Dict[str, str]:
        return self.custom_replacements_mapping

    def get_custom_replacements_count(self) -> int:
        return self.custom_replacements_count

    def reset(self):
        self.custom_replacements_mapping = {}
        self.custom_replacements_count = 0