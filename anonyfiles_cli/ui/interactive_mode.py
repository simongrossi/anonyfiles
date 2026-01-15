"""Fonctionnalités interactives pour la CLI."""

from typing import List

import typer

from .console_display import ConsoleDisplay


ENTITY_CHOICES = [
    ("PER", "Personnes"),
    ("ORG", "Organisations"),
    ("LOC", "Lieux"),
    ("EMAIL", "Emails"),
    ("DATE", "Dates"),
    ("PHONE", "Téléphones"),
    ("IBAN", "IBAN"),
    ("ADDRESS", "Adresses"),
    ("MISC", "Divers"),
]


def prompt_entities_to_exclude(console: ConsoleDisplay) -> List[str]:
    """Demande à l'utilisateur quelles entités anonymiser.

    Retourne la liste des labels à exclure en fonction du choix.
    """

    console.console.print("\n[bold]Sélectionnez les entités à anonymiser :[/bold]")
    for idx, (code, desc) in enumerate(ENTITY_CHOICES, 1):
        console.console.print(f" {idx}. {desc} ({code})")

    console.console.print("[dim]Laisser vide pour tout anonymiser.[/dim]")
    answer = typer.prompt("Numéros ou codes séparés par des virgules", default="")

    if not answer.strip():
        return []

    selections = {a.strip() for a in answer.split(",") if a.strip()}
    selected_codes: set[str] = set()

    for item in selections:
        if item.isdigit():
            index = int(item) - 1
            if 0 <= index < len(ENTITY_CHOICES):
                selected_codes.add(ENTITY_CHOICES[index][0])
            else:
                console.console.print(f"[red]Numéro invalide : {item}[/red]")
        else:
            item_up = item.upper()
            if any(code == item_up for code, _ in ENTITY_CHOICES):
                selected_codes.add(item_up)
            else:
                console.console.print(f"[red]Code inconnu : {item}[/red]")

    return [code for code, _ in ENTITY_CHOICES if code not in selected_codes]
