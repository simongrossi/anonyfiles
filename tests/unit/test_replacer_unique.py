from anonyfiles_core.anonymizer.replacer import ReplacementSession


def test_replacer_uniqueness_for_static_types():
    """
    Vérifie que des générateurs typiquement statiques (redact, placeholder)
    génèrent désormais des tokens uniques (avec index) pour des entités différentes.
    """
    session = ReplacementSession()

    # 3 entités : Paris, Lyon, Paris
    unique_spacy_entities = [
        ("Paris", "LOC"),
        ("Lyon", "LOC"),
        ("Marseille", "LOC"),
        ("Paris", "LOC"),  # Doublon
    ]

    # Règle : tout LOC devient [LOC_MASQUE]
    replacement_rules = {"LOC": {"type": "redact", "options": {"text": "[LOC_MASQUE]"}}}

    replacements, mapping = session.generate_replacements(
        unique_spacy_entities, replacement_rules
    )

    # Assertions
    # 1. Paris et Lyon doivent avoir des tokens différents
    paris_token = mapping["Paris"]
    lyon_token = mapping["Lyon"]
    marseille_token = mapping["Marseille"]

    assert paris_token != lyon_token, "Collision : Paris et Lyon ont le même token !"
    assert paris_token != marseille_token

    # 2. Les tokens doivent ressembler à [LOC_MASQUE_1], [LOC_MASQUE_2]...
    assert "_1]" in paris_token or "_2]" in paris_token or "_3]" in paris_token
    assert "_1]" in lyon_token or "_2]" in lyon_token or "_3]" in lyon_token

    # 3. La bijection : Paris doit toujours avoir le même token
    # On vérifie que dans replacements (qui contient le dernier état pour chaque entité vue), Paris est bien là
    assert replacements["Paris"] == paris_token

    print(f"\n[OK] Paris -> {paris_token}")
    print(f"[OK] Lyon -> {lyon_token}")
    print(f"[OK] Marseille -> {marseille_token}")


def test_replacer_placeholder_uniqueness():
    session = ReplacementSession()
    unique_entities = [("Alice", "PER"), ("Bob", "PER")]
    # Format simple
    replacement_rules = {
        "PER": {"type": "placeholder", "options": {"format": "{{PER}}"}}
    }

    _, mapping = session.generate_replacements(unique_entities, replacement_rules)

    t1 = mapping["Alice"]
    t2 = mapping["Bob"]

    assert t1 != t2
    # Vérifie que l'index est injecté dans le tag : {{PER}} -> {{PER_1}}
    assert "PER_1" in t1 or "PER_2" in t1
    print(f"\n[OK] Alice -> {t1}")
    print(f"[OK] Bob -> {t2}")
