import typer
from pathlib import Path
from datetime import datetime
import os
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.csv_processor import CsvProcessor
from anonymizer.txt_processor import TxtProcessor
from anonymizer.word_processor import DocxProcessor
from anonymizer.excel_processor import ExcelProcessor
from anonymizer.pdf_processor import PdfProcessor
from anonymizer.json_processor import JsonProcessor
from anonymizer.deanonymize import Deanonymizer
import yaml

app = typer.Typer()

PROCESSOR_MAP = {
    ".txt": TxtProcessor,
    ".csv": CsvProcessor,
    ".docx": DocxProcessor,
    ".xlsx": ExcelProcessor,
    ".pdf": PdfProcessor,
    ".json": JsonProcessor,
}

def load_config(config_path):
    with open(str(config_path), encoding="utf-8") as f:
        return yaml.safe_load(f)

def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def ensure_folder(folder):
    os.makedirs(folder, exist_ok=True)

def default_output(input_file, output_dir, prefix="anonymise"):
    base = input_file.stem
    ext = input_file.suffix
    folder = Path(output_dir) / "output_files"
    ensure_folder(folder)
    return folder / f"{base}_{prefix}{ext}"

def default_mapping(input_file, output_dir):
    base = input_file.stem
    folder = Path(output_dir) / "mappings"
    ensure_folder(folder)
    return folder / f"{base}_mapping_{timestamp()}.csv"

def default_log(input_file, output_dir):
    base = input_file.stem
    folder = Path(output_dir) / "log"
    ensure_folder(folder)
    return folder / f"{base}_entities_{timestamp()}.csv"

@app.command()
def anonymize(
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser"),
    config: Path = typer.Option(..., help="Fichier de configuration YAML"),
    output: Path = typer.Option(None, "--output", "-o", help="Fichier de sortie anonymisé"),
    log_entities: Path = typer.Option(None, help="Fichier CSV de log des entités détectées"),
    mapping_output: Path = typer.Option(None, help="Fichier CSV du mapping anonymisation"),
    dry_run: bool = typer.Option(False, help="Simulation sans écriture de fichiers"),
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête (ancienne option pour compatibilité CLI)"),
    has_header_opt: str = typer.Option(
        None,
        help="Spécifie explicitement si le fichier a une ligne d'entête ('true'/'false'). Prioritaire sur --csv-no-header.",
    ),
    exclude_entities: list[str] = typer.Option(None, help="Types d'entités à exclure (ex: PER,LOC)"),
    output_dir: Path = typer.Option(".", "--output-dir", help="Dossier où écrire tous les outputs")
):
    """
    Anonymise un fichier texte, tableur, bureautique ou JSON.
    """
    typer.echo(f"📂 Anonymisation du fichier : {input_file}")

    # Déterminer les chemins par défaut si non fournis
    output = output or default_output(input_file, output_dir)
    mapping_output = mapping_output or default_mapping(input_file, output_dir)
    log_entities = log_entities or default_log(input_file, output_dir)

    config_data = load_config(config)
    engine = AnonyfilesEngine(config=config_data, exclude_entities_cli=exclude_entities)

    ext = input_file.suffix.lower()
    processor_class = PROCESSOR_MAP.get(ext)
    if not processor_class:
        typer.echo(f"❌ Type de fichier non supporté : {ext}")
        raise typer.Exit(1)
    processor = processor_class()

    # Priorité à --has-header (venant du frontend/Rust), sinon compatibilité --csv-no-header
    if has_header_opt is not None:
        has_header = has_header_opt.lower() == "true"
    else:
        has_header = not csv_no_header

    typer.echo(f"[DEBUG] --has-header transmis : {has_header} (opt={has_header_opt!r}, csv_no_header={csv_no_header})")

    if ext == ".csv":
        blocks = processor.extract_blocks(input_file, has_header=has_header)
    else:
        blocks = processor.extract_blocks(input_file)

    result = engine.anonymize(
        input_path=input_file,
        output_path=output,
        entities=None,
        dry_run=dry_run,
        log_entities_path=log_entities,
        mapping_output_path=mapping_output,
    )
    if result.get("status") == "error":
        typer.echo(f"❌ Erreur : {result.get('error')}")
        raise typer.Exit(1)
    typer.echo("✅ Anonymisation terminée.")
    if result.get("entities_detected"):
        typer.echo(f"Entités détectées : {result.get('entities_detected')}")
    typer.echo(f"Fichier anonymisé : {output}")
    typer.echo(f"Mapping CSV : {mapping_output}")
    typer.echo(f"Log des entités : {log_entities}")

@app.command()
def deanonymize(
    input_file: Path = typer.Argument(..., help="Fichier à désanonymiser"),
    mapping_csv: Path = typer.Option(..., help="Mapping CSV à utiliser"),
    output: Path = typer.Option(None, help="Fichier de sortie restauré"),
    report: Path = typer.Option(None, help="Fichier de rapport détaillé"),
    dry_run: bool = typer.Option(False, help="Simulation sans écriture"),
    permissive: bool = typer.Option(False, help="Tolère les codes inconnus (restaure tout ce qu'on peut)"),
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête (première ligne)"),
):
    """
    Désanonymise un fichier anonymisé à partir d'un mapping CSV généré par anonyfiles.
    """
    typer.echo(f"🔁 Désanonymisation du fichier : {input_file}")

    strict = not permissive

    ext = input_file.suffix.lower()
    has_header = not csv_no_header

    if ext == ".csv":
        processor = CsvProcessor()
        import csv as pycsv
        with open(input_file, encoding="utf-8") as f:
            reader = pycsv.reader(f)
            rows = [row for row in reader]
        start_idx = 1 if has_header else 0
        flat_cells = [cell for row in rows[start_idx:] for cell in row]
    else:
        with open(input_file, encoding="utf-8") as f:
            flat_cells = [line.strip() for line in f if line.strip()]

    deanonymizer = Deanonymizer(str(mapping_csv), strict=strict)
    with open(input_file, encoding="utf-8") as f:
        content = f.read()
    result, report_txt = deanonymizer.deanonymize_text(content, dry_run=dry_run)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        typer.echo(f"✅ Fichier restauré écrit dans : {output}")
    if report:
        with open(report, "w", encoding="utf-8") as f:
            f.write(report_txt)
        typer.echo(f"📊 Rapport détaillé écrit dans : {report}")

if __name__ == "__main__":
    typer.echo("anonyfiles v1.6.0 (2025-05-16)")
    app()
