from faker import Faker
faker = Faker("fr_FR")

def generate_replacements(entities):
    replacements = {}
    for text, label in entities:
        if label == "PER":
            replacements[text] = faker.name()
        elif label == "LOC":
            replacements[text] = faker.city()
        elif label == "DATE":
            replacements[text] = faker.date()
        else:
            replacements[text] = "[REDACTED]"
    return replacements
