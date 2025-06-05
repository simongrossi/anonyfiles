import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_test_pdf(path):
    print(f"Création PDF vers : {path}")
    # S'assurer que le dossier existe
    os.makedirs(os.path.dirname(path), exist_ok=True)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Page 1
    c.drawString(100, height - 100, "Bonjour Pierre Dupont, vous habitez à Paris.")
    c.drawString(100, height - 120, "Votre email est pierre.dupont@example.com")
    c.drawString(100, height - 140, "Date de naissance : 12 juin 1980")

    c.showPage()

    # Page 2
    c.drawString(100, height - 100, "Deuxième page avec des entités : Jean Martin à Lyon.")
    c.drawString(100, height - 120, "Contact : jean.martin@domain.com")
    c.drawString(100, height - 140, "Rendez-vous le 1er janvier 2024")

    c.save()
    print("PDF test créé avec succès.")

if __name__ == "__main__":
    create_test_pdf("input_files/test_pdf.pdf")
