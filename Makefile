.PHONY: setup cli api gui clean test-api dev

setup:
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

	@echo "📦 Installation des dépendances pour anonyfiles_gui (si requirements.txt présent)..."
	if [ -f anonyfiles_gui/requirements.txt ]; then \
		env-gui/bin/pip install --upgrade pip setuptools wheel && \
		env-gui/bin/pip install -r anonyfiles_gui/requirements.txt; \
	else \
		echo "✅ Aucun requirements.txt dans anonyfiles_gui"; \
	fi

	@echo "✅ Tous les environnements sont prêts."

cli:
	env-cli/bin/python anonyfiles_cli/main.py anonymize tests/sample.txt --output tests/result.txt --config anonyfiles_cli/config.yaml

api:
	env-api/bin/uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port 8000 --reload

gui:
	cd anonyfiles_gui && npm run tauri dev

test-api:
	curl -X POST http://localhost:8000/anonymize/ \
	-H "Content-Type: application/json" \
	-d '{"text": "Jean Dupont habite à Paris", "anonymizePersons": true, "anonymizeLocations": true, "anonymizeOrgs": true, "anonymizeEmails": true, "anonymizeDates": true, "custom_replacement_rules": []}'

dev:
	@echo "🚀 Lancement API + GUI"
	@echo "Ouvrir deux terminaux pour exécuter 'make api' et 'make gui' séparément, ou utiliser tmux ou un superviseur."

clean:
	rm -rf env-cli env-api env-gui
