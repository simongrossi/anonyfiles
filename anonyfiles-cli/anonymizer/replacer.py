from faker import Faker
faker = Faker("fr_FR")

def generate_replacements(entities):
    replacements = {}

    for text, label in entities:
        if text in replacements:
            continue

        if label == "PER":
            replacements[text] = faker.name()

        elif label == "LOC":
            replacements[text] = faker.city()

        elif label == "DATE":
            replacements[text] = faker.date()

        elif label == "EMAIL":
            replacements[text] = faker.email()

        else:
            replacements[text] = "[REDACTED]"

    return replacements
