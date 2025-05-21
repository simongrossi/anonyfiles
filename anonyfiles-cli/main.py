# anonyfiles-cli/main.py
import typer
from pathlib import Path
from datetime import datetime
import os
import json # INDISPENSABLE pour json.loads et JSONDecodeError
from typing import Optional, List, Dict, Any # Assurez-vous que tous sont là

from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.csv_processor import CsvProcessor # Assurez-vous qu'il est importé si utilisé dans PROCESSOR_MAP
from anonymizer.txt_processor import TxtProcessor
# Décommentez les autres si PROCESSOR_MAP les utilise et que AnonyfilesEngine fait des isinstance
# from anonymizer.word_processor import DocxProcessor
# from anonymizer.excel_processor import ExcelProcessor
# from anonymizer.pdf_processor import PdfProcessor
# from anonymizer.json_processor import JsonProcessor
from anonymizer.deanonymize import Deanonymizer # Gardé de votre version originale
import yaml

app = typer.Typer()

# PROCESSOR_MAP est défini dans anonyfiles_core.py, pas besoin de le redéfinir ici
# Si vous l'aviez ici, assurez-vous qu'il correspond à celui de anonyfiles_core.py
# et que les classes sont importées.

def load_config(config_path): #
    with open(str(config_path), encoding="utf-8") as f: #
        return yaml.safe_load(f) #

def timestamp(): #
    return datetime.now().strftime("%Y%m%d-%H%M%S") #

def ensure_folder(folder): #
    os.makedirs(folder, exist_ok=True) #

def default_output(input_file, output_dir, prefix="anonymise"): #
    base = input_file.stem #
    ext = input_file.suffix #
    folder = Path(output_dir) / "output_files" #
    ensure_folder(folder) #
    return folder / f"{base}_{prefix}{ext}" #

def default_mapping(input_file, output_dir): #
    base = input_file.stem #
    folder = Path(output_dir) / "mappings" #
    ensure_folder(folder) #
    return folder / f"{base}_mapping_{timestamp()}.csv" #

def default_log(input_file, output_dir): #
    base = input_file.stem #
    folder = Path(output_dir) / "log" #
    ensure_folder(folder) #
    return folder / f"{base}_entities_{timestamp()}.csv" #

@app.command()
def anonymize( #
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser"), #
    config: Path = typer.Option(..., help="Fichier de configuration YAML"), #
    output: Path = typer.Option(None, "--output", "-o", help="Fichier de sortie anonymisé"), #
    log_entities: Path = typer.Option(None, help="Fichier CSV de log des entités détectées"), #
    mapping_output: Path = typer.Option(None, help="Fichier CSV du mapping anonymisation"), #
    dry_run: bool = typer.Option(False, help="Simulation sans écriture de fichiers"), #
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête (ancienne option pour compatibilité CLI)"), #
    has_header_opt: str = typer.Option( #
        None, #
        help="Spécifie explicitement si le fichier a une ligne d'entête ('true'/'false'). Prioritaire sur --csv-no-header.", #
    ),
    exclude_entities: list[str] = typer.Option(None, help="Types d'entités à exclure (ex: PER,LOC)"), #
    custom_replacements_json: Optional[str] = typer.Option(None, help="Chaîne JSON des règles de remplacement personnalisées"),
    output_dir: Path = typer.Option(".", "--output-dir", help="Dossier où écrire tous les outputs") #
):
    """
    Anonymise un fichier texte, tableur, bureautique ou JSON.
    """ #
    typer.echo(f"📂 Anonymisation du fichier : {input_file}") #

    output = output or default_output(input_file, output_dir) #
    mapping_output = mapping_output or default_mapping(input_file, output_dir) #
    log_entities = log_entities or default_log(input_file, output_dir) #

    config_data = load_config(config) #
    
    custom_rules_list = []
    if custom_replacements_json:
        # --- MODIFICATION ICI pour un meilleur débogage de l'erreur JSON ---
        typer.echo(f"DEBUG_MAIN_PY: Chaîne JSON brute reçue pour custom_replacements_json : >>>{custom_replacements_json}<<<")
        try:
            custom_rules_list = json.loads(custom_replacements_json)
            if not isinstance(custom_rules_list, list):
                typer.echo("AVERTISSEMENT : --custom-replacements-json n'est pas une liste valide. Règles ignorées.", err=True)
                custom_rules_list = []
        except json.JSONDecodeError as e: # Capturer l'exception pour voir le message détaillé
            typer.echo(f"ERREUR : Format JSON invalide pour --custom-replacements-json. Détail de l'erreur : {e}. Règles ignorées.", err=True)
            custom_rules_list = []
            # Optionnel: raise typer.Exit(code=1) si c'est une erreur bloquante
        # --- FIN DE LA MODIFICATION ---

    engine = AnonyfilesEngine( #
        config=config_data, #
        exclude_entities_cli=exclude_entities, #
        custom_replacement_rules=custom_rules_list 
    )
    
    processor_kwargs = {}
    if input_file.suffix.lower() == ".csv": #
        if has_header_opt is not None: #
            processor_kwargs['has_header'] = has_header_opt.lower() == "true" #
        else: #
            processor_kwargs['has_header'] = not csv_no_header #
        typer.echo(f"[DEBUG] Option 'has_header' pour CSV : {processor_kwargs.get('has_header')}") #

    result = engine.anonymize( #
        input_path=input_file,
        output_path=output, #
        entities=None, # Filtre pour les types spaCy, pas les règles custom
        dry_run=dry_run, #
        log_entities_path=log_entities, #
        mapping_output_path=mapping_output, #
        **processor_kwargs
    )

    if result.get("status") == "error": #
        typer.echo(f"❌ Erreur : {result.get('error')}") #
        raise typer.Exit(1) #
    
    typer.echo("✅ Anonymisation terminée.") #
    if result.get("entities_detected"): #
        typer.echo(f"Entités spaCy détectées (après règles custom pour TXT) : {result.get('entities_detected')}") #
    typer.echo(f"Fichier anonymisé : {output}") #
    typer.echo(f"Mapping CSV (pour entités spaCy) : {mapping_output}") #
    typer.echo(f"Log des entités (spaCy) : {log_entities}") #

@app.command()
def deanonymize( #
    input_file: Path = typer.Argument(..., help="Fichier à désanonymiser"), #
    mapping_csv: Path = typer.Option(..., help="Mapping CSV à utiliser"), #
    output: Path = typer.Option(None, help="Fichier de sortie restauré"), #
    report: Path = typer.Option(None, help="Fichier de rapport détaillé"), #
    dry_run: bool = typer.Option(False, help="Simulation sans écriture"), #
    permissive: bool = typer.Option(False, help="Tolère les codes inconnus (restaure tout ce qu'on peut)"), #
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête (première ligne)"), #
):
    """
    Désanonymise un fichier anonymisé à partir d'un mapping CSV généré par anonyfiles.
    """ #
    typer.echo(f"🔁 Désanonymisation du fichier : {input_file}") #

    strict = not permissive #

    ext = input_file.suffix.lower() #
    has_header = not csv_no_header #

    # Le reste de la fonction deanonymize est inchangé par rapport à votre version originale.
    # ... (copiez ici le reste de votre fonction deanonymize) ...
    if ext == ".csv": #
        # processor = CsvProcessor() # Pas nécessaire si on ne fait que lire le contenu à plat
        import csv as pycsv #
        with open(input_file, encoding="utf-8") as f: #
            reader = pycsv.reader(f) #
            rows = [row for row in reader] #
        start_idx = 1 if has_header else 0 #
        flat_cells = [cell for row in rows[start_idx:] for cell in row] #
    else: #
        with open(input_file, encoding="utf-8") as f: #
            # Pour deanonymize_text, on a besoin du contenu brut
            # flat_cells = [line.strip() for line in f if line.strip()] # Ce n'est pas utilisé directement par deanonymize_text
            pass # deanonymize_text lira le contenu complet plus bas

    deanonymizer = Deanonymizer(str(mapping_csv), strict=strict) #
    with open(input_file, encoding="utf-8") as f: #
        content = f.read() #
    result, report_data = deanonymizer.deanonymize_text(content, dry_run=dry_run) # `report_txt` renommé en `report_data` pour clarté

    if output: #
        with open(output, "w", encoding="utf-8") as f: #
            f.write(result) #
        typer.echo(f"✅ Fichier restauré écrit dans : {output}") #
    
    # Le rapport de Deanonymizer est un dict, il faut le formater pour l'écriture si besoin
    if report: #
        # Version simplifiée: convertir le dict en string JSON pour le rapport
        # ou utiliser la méthode generate_report de Deanonymizer si elle existe et retourne un string
        # Supposons que report_data est un dict. Pour l'écrire, on peut le sérialiser.
        report_string_content = json.dumps(report_data, indent=2, ensure_ascii=False)
        with open(report, "w", encoding="utf-8") as f: #
            f.write(report_string_content) #
        typer.echo(f"📊 Rapport détaillé écrit dans : {report}") #


if __name__ == "__main__": #
    typer.echo("anonyfiles CLI (version avec support custom rules pour TXT)")
    app() #