# tests/gen_samples_adv.py

from faker import Faker
from pathlib import Path
import csv
import json

try:
    from docx import Document
except ImportError:
    raise ImportError("Installe python-docx : pip install python-docx")

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # Gère l'absence pour le PDF

fake = Faker("fr_FR")


def gen_csv(path, n=5):
    """
    Génère un CSV avec n lignes, chaque ligne contient deux identités + des entités croisées
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "Nom1",
        "Email1",
        "DateNaiss1",
        "Ville1",
        "Entreprise1",
        "Nom2",
        "Email2",
        "DateNaiss2",
        "Ville2",
        "Entreprise2",
        "DateEvent",
        "LieuEvent",
        "Organisateur",
    ]
    data = [headers]
    for _ in range(n):
        data.append(
            [
                fake.name(),
                fake.email(),
                fake.date_of_birth().strftime("%d/%m/%Y"),
                fake.city(),
                fake.company(),
                fake.name(),
                fake.email(),
                fake.date_of_birth().strftime("%d/%m/%Y"),
                fake.city(),
                fake.company(),
                fake.date(),
                fake.city(),
                fake.company(),
            ]
        )
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"[OK] Fichier CSV généré: {path}")


def gen_docx(path, n=5):
    """
    Génère un DOCX où chaque paragraphe contient deux identités + autres entités mélangées
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for _ in range(n):
        nom1 = fake.name()
        email1 = fake.email()
        date1 = fake.date_of_birth().strftime("%d/%m/%Y")
        ville1 = fake.city()
        entreprise1 = fake.company()

        nom2 = fake.name()
        email2 = fake.email()
        date2 = fake.date_of_birth().strftime("%d/%m/%Y")
        ville2 = fake.city()
        entreprise2 = fake.company()

        date_event = fake.date()
        lieu_event = fake.city()
        organisateur = fake.company()

        paragraphe = (
            f"{nom1} ({email1}), né le {date1} à {ville1}, travaille chez {entreprise1}.\n"
            f"{nom2} ({email2}), né le {date2} à {ville2}, travaille chez {entreprise2}.\n"
            f"Ils participeront à un événement le {date_event} à {lieu_event}, organisé par {organisateur}.\n"
        )
        doc.add_paragraph(paragraphe)
    doc.save(path)
    print(f"[OK] Fichier DOCX généré: {path}")


def gen_json(path, n=5):
    """
    Génère un JSON avec des objets imbriqués et plusieurs identités par entrée
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    events = []
    for _ in range(n):
        events.append(
            {
                "event": {
                    "date": fake.date(),
                    "place": fake.city(),
                    "organizer": fake.company(),
                },
                "participants": [
                    {
                        "name": fake.name(),
                        "email": fake.email(),
                        "birth": fake.date_of_birth().strftime("%d/%m/%Y"),
                        "city": fake.city(),
                        "company": fake.company(),
                    },
                    {
                        "name": fake.name(),
                        "email": fake.email(),
                        "birth": fake.date_of_birth().strftime("%d/%m/%Y"),
                        "city": fake.city(),
                        "company": fake.company(),
                    },
                ],
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"[OK] Fichier JSON généré: {path}")


def gen_pdf(path, n=5):
    """
    Génère un PDF avec plusieurs paragraphes, chaque paragraphe contenant plusieurs identités/entités
    (Utilise PyMuPDF : pip install pymupdf)
    """
    if fitz is None:
        print("[WARN] PyMuPDF non installé, génération PDF impossible")
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for _ in range(n):
        page = doc.new_page()
        nom1 = fake.name()
        email1 = fake.email()
        date1 = fake.date_of_birth().strftime("%d/%m/%Y")
        ville1 = fake.city()
        entreprise1 = fake.company()
        nom2 = fake.name()
        email2 = fake.email()
        date2 = fake.date_of_birth().strftime("%d/%m/%Y")
        ville2 = fake.city()
        entreprise2 = fake.company()
        date_event = fake.date()
        lieu_event = fake.city()
        organisateur = fake.company()
        texte = (
            f"{nom1} ({email1}), né le {date1} à {ville1}, travaille chez {entreprise1}.\n"
            f"{nom2} ({email2}), né le {date2} à {ville2}, travaille chez {entreprise2}.\n"
            f"Ils participeront à un événement le {date_event} à {lieu_event}, organisé par {organisateur}.\n"
        )
        page.insert_text((72, 72), texte, fontsize=12)
    doc.save(path)
    print(f"[OK] Fichier PDF généré: {path}")


if __name__ == "__main__":
    gen_csv("input_files/exemple.csv", n=6)
    gen_docx("input_files/exemple.docx", n=6)
    gen_json("input_files/exemple.json", n=6)
    gen_pdf("input_files/exemple.pdf", n=6)
