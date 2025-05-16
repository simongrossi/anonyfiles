import yaml
from cerberus import Validator
from pathlib import Path

SCHEMA = {
    'spacy_model': {'type': 'string', 'required': True},
    'replacements': {
        'type': 'dict',
        'required': True,
        'valuesrules': {
            'type': 'dict',
            'schema': {
                'type': {'type': 'string', 'allowed': ['codes', 'faker', 'redact', 'placeholder'], 'required': True},
                'options': {'type': 'dict', 'required': False},
            }
        }
    },
    'exclude_entities': {
        'type': 'list',
        'required': False,
        'schema': {
            'type': 'list',
            'schema': {'type': 'string'}
        },
        'default': []
    }
}

def validate():
    config_path = Path(__file__).parent / "generated_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    v = Validator(SCHEMA)
    if v.validate(config):
        print("✅ Validation OK")
    else:
        print("❌ Validation ERROR")
        print(v.errors)

if __name__ == "__main__":
    validate()
