# anonyfiles_cli/commands/config.py

import json
import os
from pathlib import Path

import typer

from ..exceptions import ConfigurationError
from ..managers.config_manager import ConfigManager
from ..managers.validation_manager import ValidationManager
from ..ui.console_display import ConsoleDisplay
from ..utils.system_utils import open_file_in_editor  # Import de la fonction utilitaire

app = typer.Typer(help="Gère la configuration d'Anonyfiles.")
console = ConsoleDisplay()


# Définition des codes de sortie pour Typer
class ExitCodes:
    SUCCESS = 0
    USER_CANCEL = 1
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3


@app.command(name="show", help="Affiche la configuration effective actuelle.")
def show_config(
    key: str | None = typer.Option(
        None, "--key", help="Clé de configuration spécifique à afficher."
    ),
):
    """Affiche la configuration d'Anonyfiles."""
    try:
        config_data = ConfigManager.get_effective_config(
            None
        )  # Pas de CLI config pour 'show'
        if key:
            if key in config_data:
                console.console.print(f"{key}: {config_data[key]}")
            else:
                console.console.print(
                    f"❌ Clé '{key}' non trouvée dans la configuration effective.",
                    style="red",
                )
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
        else:
            console.console.print(
                "🔧 [bold]Configuration actuelle effective (fusionnée):[/bold]"
            )
            console.console.print(json.dumps(config_data, indent=2, ensure_ascii=False))

            user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
            if user_config_path.exists():
                console.console.print(
                    f"\n[dim]Fichier de configuration utilisateur : {user_config_path}[/dim]"
                )
            else:
                console.console.print(
                    "\n[dim]Aucun fichier de configuration utilisateur trouvé. La configuration par défaut est utilisée.[/dim]"
                )
    except typer.Exit:
        raise

    except Exception as e:
        console.handle_error(e, "config_show_command")
        raise typer.Exit(ExitCodes.GENERAL_ERROR)


@app.command(
    name="create", help="Crée un fichier de configuration utilisateur par défaut."
)
def create_config(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Affiche ce qui serait modifié sans écrire le fichier."
    ),
):
    """Crée un fichier de configuration utilisateur par défaut si celui-ci n'existe pas."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if dry_run:
        console.console.print(
            f"[yellow]Mode dry-run : le fichier '{user_config_path}' serait créé ou écrasé.[/yellow]"
        )
        return

    if user_config_path.exists() and not typer.confirm(
        f"⚠️ Le fichier de configuration '{user_config_path}' existe déjà. L'écraser pour recréer une config par défaut ?"
    ):
        raise typer.Exit(ExitCodes.USER_CANCEL)

    try:
        ConfigManager.create_default_user_config()
        console.console.print(
            f"✅ Configuration par défaut créée dans : [green]{user_config_path}[/green]"
        )
    except typer.Exit:
        raise

    except Exception as e:
        console.handle_error(e, "config_create_command")
        raise typer.Exit(ExitCodes.CONFIG_ERROR)


@app.command(
    name="init",
    help="Initialise la configuration d'Anonyfiles (alias convivial de reset).",
)
def init_config(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force la réinitialisation sans confirmation si une config existe déjà.",
    ),
):
    """
    Initialise ou réinitialise la configuration d'Anonyfiles.
    Idéal pour commencer avec une installation fraîche.
    """
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE

    if user_config_path.exists():
        if not force and not typer.confirm(
            f"Une configuration existe déjà à {user_config_path}. Voulez-vous la réinitialiser (écraser) ?"
        ):
            console.console.print("Initialisation annulée.")
            raise typer.Exit(ExitCodes.USER_CANCEL)

        # Suppression de l'existante si confirmée ou forcée
        try:
            os.remove(user_config_path)
        except Exception as e:
            console.console.print(
                f"[red]Erreur lors de la suppression de l'ancienne config : {e}[/red]"
            )
            raise typer.Exit(ExitCodes.GENERAL_ERROR)

    try:
        ConfigManager.create_default_user_config()
        console.console.print(
            f"✨ Configuration initialisée dans [green]{user_config_path}[/green]"
        )
    except Exception as e:
        console.handle_error(e, "config_init_command")
        raise typer.Exit(ExitCodes.CONFIG_ERROR)


@app.command(
    name="reset",
    help="Réinitialise le fichier de configuration utilisateur à ses valeurs par défaut.",
)
def reset_config(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Affiche ce qui serait modifié sans écrire le fichier."
    ),
):
    """Réinitialise le fichier de configuration utilisateur à ses valeurs par défaut."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if dry_run:
        if user_config_path.exists():
            console.console.print(
                f"[yellow]Mode dry-run : le fichier '{user_config_path}' serait supprimé puis recréé.[/yellow]"
            )
        else:
            console.console.print(
                f"[yellow]Mode dry-run : un fichier serait créé à '{user_config_path}'.[/yellow]"
            )
        return

    if user_config_path.exists():
        if typer.confirm(
            f"⚠️ Réinitialiser la configuration utilisateur ([blue]{user_config_path}[/blue]) à ses valeurs par défaut ? Cela supprimera le fichier existant."
        ):
            try:
                os.remove(user_config_path)
                ConfigManager.create_default_user_config()  # Recrée une version par défaut
                console.console.print("✅ Configuration utilisateur réinitialisée.")
            except typer.Exit:
                raise

            except Exception as e:
                console.handle_error(e, "config_reset_command")
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
        else:
            console.console.print(
                "Opération de réinitialisation annulée.", style="yellow"
            )
            raise typer.Exit(ExitCodes.USER_CANCEL)
    else:
        console.console.print(
            "ℹ️ Aucun fichier de configuration utilisateur à réinitialiser. Création d'une config par défaut.",
            style="blue",
        )
        try:
            ConfigManager.create_default_user_config()
            console.console.print(
                f"✅ Configuration par défaut créée dans : [green]{user_config_path}[/green]"
            )
        except typer.Exit:
            raise

        except Exception as e:
            console.handle_error(e, "config_reset_command")
            raise typer.Exit(ExitCodes.CONFIG_ERROR)


@app.command(
    name="edit",
    help="Ouvre le fichier de configuration utilisateur dans l'éditeur par défaut.",
)
def edit_config():
    """Ouvre le fichier de configuration utilisateur dans l'éditeur de texte par défaut du système."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if not user_config_path.exists():
        console.console.print(
            "ℹ️ Le fichier de configuration utilisateur n'existe pas. Création d'un fichier par défaut pour édition.",
            style="blue",
        )
        try:
            ConfigManager.create_default_user_config()
            console.console.print(
                f"✅ Fichier de configuration par défaut créé : [green]{user_config_path}[/green]",
                style="green",
            )
        except typer.Exit:
            raise

        except Exception as e:
            console.handle_error(e, "config_edit_command")
            raise typer.Exit(ExitCodes.CONFIG_ERROR)

    console.console.print(
        f"💡 Ouverture du fichier de configuration pour édition : [blue]{user_config_path}[/blue]"
    )
    open_file_in_editor(user_config_path)


@app.command(name="validate-config", help="Valide un fichier de configuration YAML.")
def validate_config_cmd(
    config_path: Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, readable=True
    ),
):
    """Vérifie qu'un fichier de configuration est valide."""
    try:
        ValidationManager.load_and_validate_config(config_path)
        console.console.print(f"✅ Configuration valide : [green]{config_path}[/green]")
    except ConfigurationError as e:
        console.console.print(f"❌ {e}", style="red")
        raise typer.Exit(ExitCodes.CONFIG_ERROR)
    except typer.Exit:
        raise
    except Exception as e:
        console.handle_error(e, "config_validate_command")
        raise typer.Exit(ExitCodes.GENERAL_ERROR)
