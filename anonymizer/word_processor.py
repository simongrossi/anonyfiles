from docx import Document

def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def replace_entities_in_docx(path, replacements, output_path):
    doc = Document(path)
    for p in doc.paragraphs:
        for original, replacement in replacements.items():
            if original in p.text:
                p.text = p.text.replace(original, replacement)
    doc.save(output_path)
