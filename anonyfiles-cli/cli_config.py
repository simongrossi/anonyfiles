# cli_config.py

import typer
import yaml
from pathlib import Path
from pykwalify.core import Core

app = typer.Typer(help="Gestion avancée de la configuration YAML d'anonyfiles")

# Chemin relatif vers le fichier schema.yaml (doit être dans le même dossier que ce fichier)
SCHEMA_PATH = Path(__file__).parent / "schema.yaml"

def validate_config_yaml(yaml_path: Path, schema_path: Path) -> tuple[bool, str | None]:
    """
    Valide un fichier YAML avec pykwalify selon un schema YAML.
    Retourne (True, None) si valide, (False, message d'erreur) sinon.
    """
    try:
        core = Core(source_file=str(yaml_path), schema_files=[str(schema_path)])
        core.validate()
        return True, None
    except Exception as e:
        return False, str(e)


@app.command()
def validate(
    config: Path = typer.Option(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Chemin vers le fichier YAML à valider",
    ),
):
    """
    Valide un fichier YAML de configuration anonyfiles avec le schema.
    """
    valid, error = validate_config_yaml(config, SCHEMA_PATH)
    if valid:
        typer.echo(f"✅ La configuration {config} est valide.")
    else:
        typer.secho(f"❌ Erreur de validation :\n{error}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} (y/n) : ").strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("Réponse invalide, merci de taper 'y' ou 'n'.")


def ask_choice(question: str, choices: list[str]) -> str:
    """
    Affiche une liste de choix numérotés et retourne le choix de l'utilisateur.
    """
    print(question)
    for idx, choice in enumerate(choices, 1):
        print(f"{idx}. {choice}")
    while True:
        selected = input("Votre choix (numéro) : ").strip()
        if selected.isdigit():
            selected_idx = int(selected) - 1
            if 0 <= selected_idx < len(choices):
                return choices[selected_idx]
        print(f"Choix invalide, entrez un numéro entre 1 et {len(choices)}.")


@app.command()
def wizard(
    output: Path = typer.Option(
        "config_generated.yaml",
        help="Chemin du fichier YAML à générer",
    ),
):
    """
    Assistant CLI simple pour générer un fichier config YAML anonyfiles.
    """

    typer.echo("=== Assistant de configuration anonyfiles ===")
    config = {}

    config["spacy_model"] = input(
        "Nom du modèle spaCy (ex: fr_core_news_md, fr_core_news_sm) : "
    ).strip()

    entities = ["PER", "LOC", "ORG", "DATE", "EMAIL"]
    replacements = {}
    typer.echo("\nConfiguration des règles de remplacement par entité :")
    for ent in entities:
        rep_type = ask_choice(
            f"Type de remplacement pour {ent} ?",
            ["codes", "faker", "redact", "placeholder"],
        )
        options = {}
        if rep_type == "redact":
            options["text"] = input(f"Texte de remplacement pour {ent} (ex: [REDACTED]) : ").strip()
        replacements[ent] = {"type": rep_type}
        if options:
            replacements[ent]["options"] = options
    config["replacements"] = replacements

    exclude_entities = []
    typer.echo("\nGestion des entités à exclure :")
    while ask_yes_no("Voulez-vous ajouter une entité à exclure ?"):
        text = input("Texte à exclure : ").strip()
        label = ask_choice("Label entité (ex: PER) :", entities)
        exclude_entities.append([text, label])
    config["exclude_entities"] = exclude_entities

    # Sauvegarde YAML
    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    typer.echo(f"\n✅ Configuration sauvegardée dans : {output}")


if __name__ == "__main__":
    app()
