# anonyfiles_cli/commands/utils.py

import typer
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..ui.console_display import ConsoleDisplay
from ..utils.system_utils import detect_file_encoding # Import de la fonction
from ..exceptions import AnonyfilesError # Assurez-vous d'importer les exceptions nécessaires

app = typer.Typer(help="Commandes utilitaires pour Anonyfiles.")
console = ConsoleDisplay()

# Définition des codes de sortie pour Typer
class ExitCodes:
    SUCCESS = 0
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3

@app.command(name="version", help="Affiche la version d'Anonyfiles.")
def show_version():
    """Affiche la version d'Anonyfiles."""
    console.console.print("🔧 [bold]Anonyfiles CLI[/bold] - Version 1.2.0") # Mise à jour de la version
    console.console.print("Outil d'anonymisation de fichiers basé sur spaCy")
    console.console.print("📚 Documentation: https://github.com/simongrossi/anonyfiles")

@app.command(name="list-entities", help="Liste les types d'entités supportées par spaCy.")
def list_entities():
    """Liste les types d'entités supportées par spaCy."""
    entities = {
        "PER": "Personnes (noms, prénoms)",
        "ORG": "Organisations (entreprises, institutions)",
        "LOC": "Lieux (villes, pays, adresses)",
        "MISC": "Divers (codes, références)",
        "DATE": "Dates et heures",
        "EMAIL": "Adresses email",
        "PHONE": "Numéros de téléphone",
        "URL": "URLs et liens web",
        "IBAN": "Numéros IBAN",
        "ADDRESS": "Adresses complètes"
    }
    
    console.console.print("📋 [bold]Types d'entités supportées par Anonyfiles CLI:[/bold]")
    for code, desc in entities.items():
        console.console.print(f"  • [cyan]{code}[/cyan]: {desc}")

@app.command(name="info", help="Affiche des informations détaillées sur un fichier.")
def file_info(
    input_file: Path = typer.Argument(..., help="Fichier à analyser", exists=True, file_okay=True, dir_okay=False, readable=True)
):
    """Affiche des informations détaillées sur un fichier sans le traiter."""
    console.console.print(f"📋 [bold]Analyse de : {input_file.name}[/bold]")
    
    try:
        stat = input_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        
        console.console.print(f"📁 Taille : {stat.st_size:,} octets ({size_mb:.2f} MB)")
        console.console.print(f"📄 Extension : {input_file.suffix}")
        console.console.print(f"📅 Modifié : {datetime.fromtimestamp(stat.st_mtime)}")
        
        # Aperçu du contenu avec détection d'encodage via le nouveau module
        encoding = detect_file_encoding(input_file)
        console.console.print(f"🔤 Encodage détecté : [yellow]{encoding}[/yellow]")

        content = ""
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                content = f.read(1000)  # Premier Ko
                lines = content.count('\n') + 1
            
            console.console.print(f"📝 Lignes (approx.) : {lines}")
            
            preview = content[:200] + "..." if len(content) > 200 else content
            console.console.print(f"\n📖 [dim]Aperçu :[/dim]\n{preview}")
            
        except UnicodeDecodeError:
            console.console.print("⚠️ Fichier binaire ou encodage non textuel/détecté. Impossible d'afficher l'aperçu textuel.", style="yellow")
        except Exception as e:
            console.console.print(f"❌ Erreur de lecture du contenu : {e}", style="red")

    except Exception as e:
        console.handle_error(e, "file_info_command")
        raise typer.Exit(code=ExitCodes.GENERAL_ERROR)


@app.command(name="benchmark", help="Teste les performances d'anonymisation sur un fichier donné.")
def run_benchmark(
    test_file: Path = typer.Argument(..., help="Fichier de test à utiliser pour le benchmark.", exists=True, file_okay=True, dir_okay=False, readable=True),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Nombre d'itérations pour le benchmark."),
    config: Optional[Path] = typer.Option(None, "--config", help="Fichier de configuration YAML à tester pour le benchmark.", exists=True, file_okay=True, dir_okay=False, readable=True)
):
    """
    Teste les performances d'anonymisation d'Anonyfiles sur un fichier spécifique.
    """
    from ..handlers.anonymize_handler import AnonymizeHandler # Import local pour éviter les imports circulaires si ce handler dépend de benchmark
    from ..managers.config_manager import ConfigManager # Pour la config
    
    console.console.print(f"🚀 [bold]Benchmark d'anonymisation[/bold]")
    console.console.print(f"📄 Fichier : [cyan]{test_file.name}[/cyan]")
    console.console.print(f"🔄 Itérations : [yellow]{iterations}[/yellow]")
    
    times = []
    
    # Préparez un AnonymizeHandler pour le benchmark (peut-être en mode silencieux)
    benchmark_handler = AnonymizeHandler(console) # Passe la console pour l'affichage interne
    
    for i in range(iterations):
        console.console.print(f"[{i+1}/{iterations}] Traitement de l'itération...")
        
        start_time = time.time() # Importez 'time' si ce n'est pas déjà fait
        
        try:
            # Récupérer la config effective (avec la possibilité d'une config passée en paramètre)
            effective_config = ConfigManager.get_effective_config(config)

            # Appel direct à la logique d'anonymisation du handler en mode dry_run
            # On passe None pour les chemins de sortie car on ne veut pas écrire de fichiers réels
            success = benchmark_handler.process(
                input_file=test_file,
                config_path=config, # Passe le chemin de config pour que le handler le gère
                output=None,
                log_entities=None,
                mapping_output=None,
                output_dir=Path("."), # Un répertoire temporaire factice si nécessaire
                dry_run=True,  # IMPORTANT : Mode dry_run pour ne mesurer que le traitement
                csv_no_header=False, # Supposons un défaut pour le benchmark, ou ajouter une option
                has_header_opt=None, # Supposons un défaut pour le benchmark
                exclude_entities=None, # Laisser l'engine AnonyfilesEngine décider
                custom_replacements_json=None, # Laisser l'engine AnonyfilesEngine décider
                append_timestamp=False, # Pas pertinent en dry_run
                force=True # Pas pertinent en dry_run
            )
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            if success:
                console.console.print(f"  ⏱️ [green]{duration:.2f}s[/green] - Traitement terminé.")
            else:
                console.console.print(f"  ❌ Erreur pendant l'itération, temps mesuré : {duration:.2f}s", style="red")
            
        except Exception as e:
            console.console.print(f"  ❌ Erreur inattendue lors du benchmark : [red]{e}[/red]", style="red")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        console.console.print(f"\n📊 [bold]Résultats du Benchmark:[/bold]")
        console.console.print(f"⏱️ Temps moyen : [cyan]{avg_time:.2f}s[/cyan]")
        console.console.print(f"🚀 Plus rapide : [green]{min_time:.2f}s[/green]")
        console.console.print(f"🐌 Plus lent : [red]{max_time:.2f}s[/red]")