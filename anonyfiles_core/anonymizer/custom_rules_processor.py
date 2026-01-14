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

                # Optimisation: Compilation unique des regex au chargement
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
        Utilise les expressions régulières compilées pour une performance optimale.
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
                    # Utilisation de la méthode .sub() avec un callback pour une performance maximale
                    # et pour pouvoir logger chaque remplacement individuellement.
                    def replacement_handler(match):
                        original_text = match.group(0)
                        
                        # Gérer l'expansion des groupes si le remplacement contient des backreferences (ex: \1)
                        try:
                            final_replacement = match.expand(replacement)
                        except re.error:
                            # Fallback si le template est invalide, on utilise le littéral
                            final_replacement = replacement

                        self.audit_logger.log(original_text, final_replacement, "custom_regex", 1, original_text=original_text)
                        self.custom_replacements_count += 1
                        self.custom_replacements_mapping[original_text] = final_replacement
                        return final_replacement

                    modified_text = compiled_pattern.sub(replacement_handler, modified_text)

                else:
                    # Simple text replacement (str.replace est très optimisé pour les littéraux)
                    count = modified_text.count(pattern_str)
                    if count > 0:
                        modified_text = modified_text.replace(pattern_str, replacement)
                        self.audit_logger.log(pattern_str, replacement, "custom_text", count, original_text=pattern_str)
                        self.custom_replacements_count += count
                        self.custom_replacements_mapping[pattern_str] = replacement

            except Exception as e:
                # Catch-all pour éviter de crasher tout le process si une règle spécifique échoue
                typer.echo(f"ERREUR (CustomRulesProcessor): Échec application règle '{pattern_str}': {e}", err=True)
                
        return modified_text

    def get_custom_replacements_mapping(self) -> Dict[str, str]:
        return self.custom_replacements_mapping

    def get_custom_replacements_count(self) -> int:
        return self.custom_replacements_count

    def reset(self):
        self.custom_replacements_mapping = {}
        self.custom_replacements_count = 0
