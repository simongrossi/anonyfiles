
import logging
import shutil
import json
from pathlib import Path
from anonyfiles_core import AnonyfilesEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

# Paths
INPUT_FILE = Path(__file__).parent / "complex_input.txt"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "complex_input_anonymized.txt"
MAPPING_FILE = OUTPUT_DIR / "mapping.csv" # Engine uses CSV by default

def run_test():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print(f"Running anonymization on {INPUT_FILE}...")
    
    # Init Engine (defaults)
    # Using defaults: redacts/replaces common entities found by Spacy FR model
    engine = AnonyfilesEngine(config={})
    
    result = engine.anonymize(
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        mapping_output_path=MAPPING_FILE,
        entities=None,
        dry_run=False,
        log_entities_path=None
    )
    
    if result["status"] != "success":
        print(f"ERROR: {result.get('error')}")
        return

    print("Anonymization finished.")
    
    # Read output content
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("\n--- START ANONYMIZED CONTENT ---")
    print(content)
    print("--- END ANONYMIZED CONTENT ---\n")
    
    # Verify Uniqueness Logic via Mapping File (CSV)
    # Mapping CSV format is: Original,Anonymized
    import csv
    mapping_dict = {}
    with open(MAPPING_FILE, "r", encoding="utf-8", newline='') as f:
        reader = csv.reader(f)
        try:
            next(reader) # Skip header if present (Engine usually puts "Original,Replacement")
        except StopIteration:
            pass
        for row in reader:
            if len(row) >= 2:
                mapping_dict[row[0]] = row[1]
    
    print("--- MAPPING KEYS DETECTED ---")
    for k in mapping_dict.keys():
        print(f"Key: '{k}' -> '{mapping_dict[k]}'")
    print("----------------------------")
    
    # Check specific uniqueness cases based on input text
    # "Paris" vs "Lyon" vs "Toulouse" vs "Bordeaux"
    cities = ["Paris", "Lyon", "Toulouse", "Bordeaux"]
    city_tokens = {}
    for city in cities:
        if city in mapping_dict:
            city_tokens[city] = mapping_dict[city]
            print(f"City '{city}' -> {city_tokens[city]}")
        else:
            print(f"WARNING: City '{city}' not found in mapping (maybe not detected by SpaCy?).")
            
    # Check that discovered tokens are distinct
    found_tokens = list(city_tokens.values())
    unique_found_tokens = set(found_tokens)
    if len(found_tokens) == len(unique_found_tokens):
         print("SUCCESS: mapped cities have unique tokens.")
    else:
         print(f"FAIL: Duplicate tokens found for cities! {found_tokens}")

    # Check consistency for duplicates
    # "Jean Dupont" appears in: 
    # - "Monsieur Jean Dupont habite..."
    # - "Données en double : - Monsieur Jean Dupont"
    # Spacy usually detects "Jean Dupont" as PER.
    person = "Jean Dupont"
    if person in mapping_dict:
        token = mapping_dict[person]
        print(f"Person '{person}' -> {token}")
        
        # Verify strict replacement in text
        count_in_text = content.count(token)
        print(f"Token '{token}' appears {count_in_text} times in text.")
        if count_in_text >= 2:
            print("SUCCESS: Token reused for duplicate entity.")
        else:
            print("WARNING: Token appeared less than expected (maybe text was detected differently each time?)")
    else:
        print(f"WARNING: '{person}' not found in mapping.")

if __name__ == "__main__":
    run_test()
