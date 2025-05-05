import pandas as pd

def extract_text_from_excel(path):
    df = pd.read_excel(path)
    return df.astype(str).values.flatten().tolist()

def replace_entities_in_excel(path, replacements, output_path):
    df = pd.read_excel(path)
    df = df.applymap(lambda cell: str(cell).replace(original, replacement)
                     if isinstance(cell, str) else cell
                     for original, replacement in replacements.items())
    df.to_excel(output_path, index=False)
