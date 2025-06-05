# anonyfiles_cli/commands/config.py

import typer
from pathlib import Path
import json
import os
from typing import Optional

from ..managers.config_manager import ConfigManager
from ..ui.console_display import ConsoleDisplay
from ..utils.system_utils import open_file_in_editor # Import de la fonction utilitaire
from ..exceptions import AnonyfilesError, ConfigurationError

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
    key: Optional[str] = typer.Option(None, "--key", help="Clé de configuration spécifique à afficher.")
):
    """Affiche la configuration d'Anonyfiles."""
    try:
        config_data = ConfigManager.get_effective_config(None) # Pas de CLI config pour 'show'
        if key:
            if key in config_data:
                console.console.print(f"{key}: {config_data[key]}")
            else:
                console.console.print(f"❌ Clé '{key}' non trouvée dans la configuration effective.", style="red")
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
        else:
            console.console.print("🔧 [bold]Configuration actuelle effective (fusionnée):[/bold]")
            console.console.print(json.dumps(config_data, indent=2, ensure_ascii=False))
            
            user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
            if user_config_path.exists():
                console.console.print(f"\n[dim]Fichier de configuration utilisateur : {user_config_path}[/dim]")
            else:
                console.console.print(f"\n[dim]Aucun fichier de configuration utilisateur trouvé. La configuration par défaut est utilisée.[/dim]")
    except Exception as e:
        console.handle_error(e, "config_show_command")
        raise typer.Exit(ExitCodes.GENERAL_ERROR)

@app.command(name="create", help="Crée un fichier de configuration utilisateur par défaut.")
def create_config():
    """Crée un fichier de configuration utilisateur par défaut si celui-ci n'existe pas."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if user_config_path.exists() and not typer.confirm(f"⚠️ Le fichier de configuration '{user_config_path}' existe déjà. L'écraser pour recréer une config par défaut ?"):
        raise typer.Exit(ExitCodes.USER_CANCEL)
    
    try:
        ConfigManager.create_default_user_config()
        console.console.print(f"✅ Configuration par défaut créée dans : [green]{user_config_path}[/green]")
    except Exception as e:
        console.handle_error(e, "config_create_command")
        raise typer.Exit(ExitCodes.CONFIG_ERROR)

@app.command(name="reset", help="Réinitialise le fichier de configuration utilisateur à ses valeurs par défaut.")
def reset_config():
    """Réinitialise le fichier de configuration utilisateur à ses valeurs par défaut."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if user_config_path.exists():
        if typer.confirm(f"⚠️ Réinitialiser la configuration utilisateur ([blue]{user_config_path}[/blue]) à ses valeurs par défaut ? Cela supprimera le fichier existant."):
            try:
                os.remove(user_config_path)
                ConfigManager.create_default_user_config() # Recrée une version par défaut
                console.console.print("✅ Configuration utilisateur réinitialisée.")
            except Exception as e:
                console.handle_error(e, "config_reset_command")
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
        else:
            console.console.print("Opération de réinitialisation annulée.", style="yellow")
            raise typer.Exit(ExitCodes.USER_CANCEL)
    else:
        console.console.print(f"ℹ️ Aucun fichier de configuration utilisateur à réinitialiser. Création d'une config par défaut.", style="blue")
        try:
            ConfigManager.create_default_user_config()
            console.console.print(f"✅ Configuration par défaut créée dans : [green]{user_config_path}[/green]")
        except Exception as e:
            console.handle_error(e, "config_reset_command")
            raise typer.Exit(ExitCodes.CONFIG_ERROR)

@app.command(name="edit", help="Ouvre le fichier de configuration utilisateur dans l'éditeur par défaut.")
def edit_config():
    """Ouvre le fichier de configuration utilisateur dans l'éditeur de texte par défaut du système."""
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if not user_config_path.exists():
        console.console.print(f"ℹ️ Le fichier de configuration utilisateur n'existe pas. Création d'un fichier par défaut pour édition.", style="blue")
        try:
            ConfigManager.create_default_user_config()
            console.console.print(f"✅ Fichier de configuration par défaut créé : [green]{user_config_path}[/green]", style="green")
        except Exception as e:
            console.handle_error(e, "config_edit_command")
            raise typer.Exit(ExitCodes.CONFIG_ERROR)
            
    console.console.print(f"💡 Ouverture du fichier de configuration pour édition : [blue]{user_config_path}[/blue]")
    open_file_in_editor(user_config_path)
