# anonyfiles_cli/anonymizer/audit.py

class AuditLogger:
    def __init__(self):
        self.entries = []

    def log(self, pattern, replacement, typ, count, original_text: str = None): # Ajout de original_text
        # Regroupe les remplacements identiques
        # La clé de regroupement doit maintenant inclure original_text si fourni,
        # pour éviter de regrouper des remplacements "custom" qui auraient le même pattern mais des originaux différents
        # (même si pour les règles custom, le pattern *est* l'original dans ce contexte).
        # Pour simplifier, on garde le regroupement par pattern/replacement/type.
        # original_text sera principalement pour le mapping final si différent du pattern.
        
        for entry in self.entries:
            if entry['pattern'] == pattern and entry['replacement'] == replacement and entry['type'] == typ:
                entry['count'] += count
                return
        
        entry = {
            "pattern": pattern,
            "replacement": replacement,
            "type": typ,
            "count": count
        }
        if original_text is not None:
            entry["original_text_for_custom_rule"] = original_text # Conserver l'original si pertinent pour les règles custom
        self.entries.append(entry)

    def summary(self):
        return self.entries

    def total(self):
        return sum(e["count"] for e in self.entries)

    def reset(self):
        self.entries = []