# anonyfiles_cli/anonymizer/audit.py

class AuditLogger:
    def __init__(self):
        self.entries = []

    def log(self, pattern, replacement, typ, count):
        # Regroupe les remplacements identiques
        for entry in self.entries:
            if entry['pattern'] == pattern and entry['replacement'] == replacement and entry['type'] == typ:
                entry['count'] += count
                return
        self.entries.append({
            "pattern": pattern,
            "replacement": replacement,
            "type": typ,
            "count": count
        })

    def summary(self):
        return self.entries

    def total(self):
        return sum(e["count"] for e in self.entries)

    def reset(self):
        self.entries = []
