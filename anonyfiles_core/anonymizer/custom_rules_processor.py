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
                
                # Initialisation d'un compteur spécifique à cette règle
                rule["match_counter"] = 0

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
        Garantit l'unicité des tokens générés (bijectivité).
        """
        if not self.custom_rules:
            return text_block

        modified_text = text_block
        for rule in self.custom_rules:
            pattern_str = rule.get("pattern")
            replacement_base = rule.get("replacement", "[CUSTOM_REDACTED]")
            is_regex = rule.get("isRegex", False)
            compiled_pattern: Optional[re.Pattern] = rule.get("compiled_pattern")
            
            if not pattern_str:
                continue

            try:
                if is_regex and compiled_pattern is not None:
                    # Callback unifié pour gérer la logique d'unicité
                    def replacement_handler(match):
                        original_text = match.group(0)
                        
                        # Vérifier si on a déjà tokenisé ce texte précis
                        if original_text in self.custom_replacements_mapping:
                            return self.custom_replacements_mapping[original_text]
                        
                        # Sinon, générer un nouveau token unique
                        rule["match_counter"] += 1
                        current_count = rule["match_counter"]
                        
                        # Gestion basique du template remplacement
                        try:
                             # Note: match.expand ne peut pas être utilisé facilement si on modifie dynamically le remplacement
                             # On suppose ici que replacement_base est statique ou contient des groupes simples.
                             # Pour injecter le compteur, on l'ajoute à la fin.
                             
                             # Heuristique : Si le remplacement finit par ] ou }, on insère avant
                             if replacement_base.endswith("]") or replacement_base.endswith("}"):
                                 final_token = f"{replacement_base[:-1]}_{current_count}{replacement_base[-1]}"
                             else:
                                 final_token = f"{replacement_base}_{current_count}"
                             
                             # Si backreferences nécessaires, c'est plus complexe car le compteur ferait partie du texte.
                             # Ici on simplifie : le custom rule est un TAG.
                        except Exception:
                            final_token = f"{replacement_base}_{current_count}"

                        self.audit_logger.log(original_text, final_token, "custom_regex", 1, original_text=original_text)
                        self.custom_replacements_count += 1
                        self.custom_replacements_mapping[original_text] = final_token
                        return final_token

                    modified_text = compiled_pattern.sub(replacement_handler, modified_text)

                else:
                    # Remplacement texte simple
                    # Problème : str.replace remplace TOUTES les occurrences d'un coup.
                    # Pour garantir l'unicité (bijectivité), il faut que "A" -> "T1", "A" -> "T1" (ça c'est ok).
                    # Mais si on a plusieurs occurrences de "A", elles deviennent toutes "T1". C'est correct pour la bijection.
                    # Le problème c'est que str.replace ne permet pas d'incrémenter globalement si c'est la 1ère fois qu'on voit ce mot
                    # vs la 2ème fois qu'on le voit dans un autre bloc, mais on veut garder le MÊME token.
                    
                    # Approche : On vérifie si pattern_str est dans le mapping.
                    if pattern_str in self.custom_replacements_mapping:
                        token = self.custom_replacements_mapping[pattern_str]
                    else:
                        rule["match_counter"] += 1
                        current_count = rule["match_counter"]
                        if replacement_base.endswith("]") or replacement_base.endswith("}"):
                             token = f"{replacement_base[:-1]}_{current_count}{replacement_base[-1]}"
                        else:
                             token = f"{replacement_base}_{current_count}"
                        
                        self.custom_replacements_mapping[pattern_str] = token
                        # Log pour la première occurrence (ou à chaque fois ?) 
                        # Audit log attend généralement un log par substitution.
                    
                    count = modified_text.count(pattern_str)
                    if count > 0:
                        modified_text = modified_text.replace(pattern_str, token)
                        self.audit_logger.log(pattern_str, token, "custom_text", count, original_text=pattern_str)
                        self.custom_replacements_count += count

            except Exception as e:
                typer.echo(f"ERREUR (CustomRulesProcessor): Échec application règle '{pattern_str}': {e}", err=True)
                
        return modified_text

    def get_custom_replacements_mapping(self) -> Dict[str, str]:
        return self.custom_replacements_mapping

    def get_custom_replacements_count(self) -> int:
        return self.custom_replacements_count

    def reset(self):
        self.custom_replacements_mapping = {}
        self.custom_replacements_count = 0
