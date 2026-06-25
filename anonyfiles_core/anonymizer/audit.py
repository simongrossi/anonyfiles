# anonyfiles_cli/anonymizer/audit.py

from .type_defs import AuditEntry


class AuditLogger:
    def __init__(self) -> None:
        # Utilise maintenant un dictionnaire indexé par (pattern, replacement, type)
        # pour regrouper plus facilement les entrées identiques
        self.entries: dict[tuple[str, str, str], AuditEntry] = {}

    def log(
        self,
        pattern: str,
        replacement: str,
        typ: str,
        count: int,
        original_text: str | None = None,
    ) -> None:  # Ajout de original_text
        # Regroupe les remplacements identiques
        # La clé de regroupement doit maintenant inclure original_text si fourni,
        # pour éviter de regrouper des remplacements "custom" qui auraient le même pattern mais des originaux différents
        # (même si pour les règles custom, le pattern *est* l'original dans ce contexte).
        # Pour simplifier, on garde le regroupement par pattern/replacement/type.
        # original_text sera principalement pour le mapping final si différent du pattern.

        key = (pattern, replacement, typ)
        # Si l'entrée existe déjà, on incrémente simplement le compteur
        if key in self.entries:
            self.entries[key]["count"] += count
        else:
            entry: AuditEntry = {
                "pattern": pattern,
                "replacement": replacement,
                "type": typ,
                "count": count,
            }
            if original_text is not None:
                entry["original_text_for_custom_rule"] = (
                    original_text  # Conserver l'original si pertinent pour les règles custom
                )
            self.entries[key] = entry

    def summary(self) -> list[AuditEntry]:
        # Retourne la liste des entrées déjà regroupées
        return list(self.entries.values())

    def total(self) -> int:
        return sum(e["count"] for e in self.entries.values())

    def reset(self) -> None:
        self.entries = {}
