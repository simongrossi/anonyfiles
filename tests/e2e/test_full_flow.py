import pytest
import shutil
from pathlib import Path
from pypdf import PdfReader
from anonyfiles_core import AnonyfilesEngine

# Chemin des ressources de test
TEST_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "assets"
INPUT_PDF = TEST_ASSETS_DIR / "sample.pdf"
OUTPUT_DIR = Path(__file__).resolve().parent / "output_e2e"


@pytest.fixture(scope="module")
def setup_test_env():
    """Prépare l'environnement de test : crée le dossier de sortie."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Créer un PDF factice si sample.pdf n'existe pas
    if not INPUT_PDF.exists():
        INPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(INPUT_PDF))
        c.drawString(100, 750, "Ceci est un document confidentiel de Jean Dupont.")
        c.drawString(100, 730, "Contact: jean.dupont@email.com")
        c.save()

    yield

    # Nettoyage après les tests (optionnel, commenté pour garder les artefacts en cas d'échec)
    # shutil.rmtree(OUTPUT_DIR)


def test_full_anonymization_flow(setup_test_env):
    """
    Test E2E complet :
    1. Initialise le moteur Core.
    2. Lance l'anonymisation sur un PDF.
    3. Vérifie la présence des fichiers de sortie.
    4. Vérifie l'intégrité binaire du PDF généré.
    """

    # 1. Configuration et Initialisation
    output_pdf_path = OUTPUT_DIR / "sample_anonymized.pdf"
    mapping_path = OUTPUT_DIR / "mapping.csv"
    log_path = OUTPUT_DIR / "entities.csv"

    config = {
        "spacy_model": "fr_core_news_md",
        "replacements": {
            "PER": {"type": "redact", "options": {"text": "[NOM_MASQUÉ]"}},
            "EMAIL": {"type": "redact", "options": {"text": "[EMAIL_MASQUÉ]"}},
        },
    }

    engine = AnonyfilesEngine(config=config)

    # 2. Exécution de l'anonymisation
    print(f"\n[E2E] Lancement de l'anonymisation sur : {INPUT_PDF}")
    result = engine.anonymize(
        input_path=INPUT_PDF,
        output_path=output_pdf_path,
        mapping_output_path=mapping_path,
        log_entities_path=log_path,
    )

    # 3. Vérifications fichiers
    assert (
        result["status"] == "success"
    ), f"Le moteur a retourné une erreur : {result.get('error')}"
    assert output_pdf_path.exists(), "Le fichier PDF anonymisé n'a pas été créé."
    assert mapping_path.exists(), "Le fichier de mapping n'a pas été créé."

    # 4. Vérification intégrité PDF
    print(f"[E2E] Vérification de l'intégrité du PDF généré : {output_pdf_path}")
    try:
        reader = PdfReader(output_pdf_path)
        assert len(reader.pages) > 0, "Le PDF généré est vide (0 pages)."

        # Tentative d'extraction de texte pour s'assurer que le contenu est lisible/parsable
        page_text = reader.pages[0].extract_text()
        print(f"[E2E] Texte extrait du PDF anonymisé (extrait) : {page_text[:100]}...")

        # Vérification optionnelle que la redaction a fonctionné (selon le moteur utilisé, ici PyMuPDF fait du masquage graphique)
        # Mais le texte sous-jacent peut ou non être supprimé selon l'implémentation de PdfProcessor.
        # Ce test valide principalement que le fichier est un PDF valide qui s'ouvre.

    except Exception as e:
        pytest.fail(f"Le PDF généré est corrompu ou illisible : {e}")

    print("\n[E2E] Test terminé avec succès.")
