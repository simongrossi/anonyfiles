.PHONY: setup spacy-models cli api gui clean test-api dev

setup:
	@echo "🔧 Installation des dépendances système..."
	sudo apt update
	sudo apt install -y python3 python3-venv python3-pip curl

	@if ! command -v npm >/dev/null 2>&1; then \
		echo "🧰 Installation de Node.js + npm..."; \
		curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && \
		sudo apt install -y nodejs; \
	else \
		echo "✅ Node.js et npm déjà installés."; \
	fi

	@echo "🔧 Création des environnements virtuels..."
	python3 -m venv env-cli
	python3 -m venv env-api
	python3 -m venv env-gui

	@echo "📦 Installation des dépendances pour anonyfiles_cli..."
	env-cli/bin/pip install --upgrade pip setuptools wheel
	env-cli/bin/pip install -r anonyfiles_cli/requirements.txt

	@echo "📦 Installation des dépendances pour anonyfiles_api..."
	env-api/bin/pip install --upgrade pip setuptools wheel
	env-api/bin/pip install -r anonyfiles_api/requirements.txt

	@echo "📦 Téléchargement du modèle spaCy fr_core_news_md..."
	env-api/bin/python -m spacy download fr_core_news_md

	@echo "📦 Installation des dépendances pour anonyfiles_gui (si requirements.txt présent)..."
	if [ -f anonyfiles_gui/requirements.txt ]; then \
		env-gui/bin/pip install --upgrade pip setuptools wheel && \
		env-gui/bin/pip install -r anonyfiles_gui/requirements.txt; \
	else \
		echo "✅ Aucun requirements.txt dans anonyfiles_gui"; \
	fi

	@echo "📦 Installation des modules npm pour anonyfiles_gui..."
	cd anonyfiles_gui && npm install

	@echo "✅ Tous les environnements sont prêts."

spacy-models:
	@echo "📦 Téléchargement du modèle spaCy fr_core_news_md..."
	env-api/bin/python -m spacy download fr_core_news_md

cli:
	env-cli/bin/python anonyfiles_cli/main.py anonymize tests/sample.txt --output tests/result.txt --config anonyfiles_cli/config.yaml

api:
	env-api/bin/uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port 8000 --reload

# Génère les fichiers statiques de la GUI (build web)
gui:
	cd anonyfiles_gui && npm run build

test-api:
	curl -X POST http://83.228.198.65:8000/api/anonymize/ \
	-F "file=@tests/sample.txt;type=text/plain" \
	-F 'config_options={"anonymizePersons":true,"anonymizeLocations":true,"anonymizeOrgs":true,"anonymizeEmails":true,"anonymizeDates":true,"custom_replacement_rules":[]}' \
	-F "file_type=txt"

dev:
	@echo "🚀 Lancement API + build GUI"
	@echo "Exécute 'make api' pour lancer l’API, et 'make gui' pour générer les fichiers frontend statiques."

clean:
	rm -rf env-cli env-api env-gui
