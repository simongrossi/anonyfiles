import json
import os


def create_test_json(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "name": "Jean Dupont",
        "email": "jean.dupont@example.com",
        "address": "10 rue de Paris",
        "notes": "Rendez-vous le 15 mars 2025.",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON test créé : {path}")


if __name__ == "__main__":
    create_test_json("input_files/exemple.json")
