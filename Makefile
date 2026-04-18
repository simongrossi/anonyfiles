.PHONY: setup install-deps-debian spacy-models cli api gui clean test-api dev systemd-install systemd-start systemd-stop systemd-status sidecar desktop env-pkg

install-deps-debian:
	@echo "🔧 [Debian/Ubuntu Only] Installation des dépendances système..."
	@echo "⚠️  Attention : Cette commande nécessite des droits root (sudo)."
	sudo apt update
	sudo apt install -y python3 python3-venv python3-pip curl
	@if ! command -v npm >/dev/null 2>&1; then \
		echo "🧰 Installation de Node.js + npm..."; \
		curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && \
		sudo apt install -y nodejs; \
	else \
		echo "✅ Node.js et npm déjà installés."; \
	fi

setup:
	@echo "🔧 Création des environnements virtuels..."
	python3 -m venv env-cli
	python3 -m venv env-api
	python3 -m venv env-gui

	@echo "📦 Installation des dépendances pour anonyfiles_cli..."
	env-cli/bin/pip install --upgrade pip setuptools wheel
	# Installation via pyproject.toml (mode dev)
	env-cli/bin/pip install -e .[dev]

	@echo "📦 Installation des dépendances pour anonyfiles_api..."
	env-api/bin/pip install --upgrade pip setuptools wheel
	# Installation via pyproject.toml
	env-api/bin/pip install -e .

	@echo "📦 Installation des dépendances pour anonyfiles_gui (si requirements.txt présent)..."
	if [ -f anonyfiles_gui/requirements.txt ]; then \
		env-gui/bin/pip install --upgrade pip setuptools wheel && \
		env-gui/bin/pip install -r anonyfiles_gui/requirements.txt; \
	else \
		echo "✅ Aucun requirements.txt dans anonyfiles_gui"; \
	fi

	@echo "📦 Installation des modules npm pour anonyfiles_gui..."
	# On suppose que npm est installé via install-deps-debian ou manuellement
	if command -v npm >/dev/null 2>&1; then \
		cd anonyfiles_gui && npm install; \
	else \
		echo "⚠️  npm non trouvé. Impossible d'installer les dépendances GUI. Lancez d'abord 'make install-deps-debian' ou installez Node.js manuellement."; \
	fi

	$(MAKE) spacy-models

	@echo "✅ Tous les environnements sont prêts."

spacy-models:
	@echo "📦 Téléchargement des modèles spaCy nécessaires (fr_core_news_md)..."
	env-cli/bin/python3 -m spacy download fr_core_news_md

cli:
	env-cli/bin/anonyfiles-cli anonymize tests/sample.txt --output tests/result.txt --config anonyfiles_core/config/config.yaml

api:
	env-api/bin/uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port 8000 --reload

gui:
	cd anonyfiles_gui && npm run build

tui:
	env-cli/bin/anonyfiles-cli logs interactive

setup-cli:
	@echo "📦 Installation/Mise à jour de la CLI..."
	env-cli/bin/pip install -e .

reinstall-cli:
	@echo "📦 Réinstallation propre de la CLI..."
	env-cli/bin/pip uninstall -y anonyfiles || true
	env-cli/bin/pip install -e .

test-api:
	@echo "🔗 Envoi du fichier vers $${API_URL:-http://localhost:8000}"
	curl -X POST $${API_URL:-http://localhost:8000}/anonymize/ \
		-F "file=@tests/sample.txt;type=text/plain" \
		-F 'config_options={"anonymizePersons":true,"anonymizeLocations":true,"anonyfilesOrgs":true,"anonymizeEmails":true,"anonymizeDates":true,"custom_replacement_rules":[]}' \
		-F "file_type=txt"

dev:
	@echo "🚀 Lancement API + build GUI"
	@echo "Exécute 'make api' pour lancer l’API, et 'make gui' pour générer les fichiers frontend statiques."

clean:
	rm -rf env-cli env-api env-gui

systemd-install:
	sudo cp deploy/anonyfiles-api.service /etc/systemd/system/anonyfiles-api.service
	sudo systemctl daemon-reload
	@echo "Service systemd installé. Tu peux maintenant faire 'make systemd-start'"

systemd-start:
	sudo systemctl start anonyfiles-api.service
	sudo systemctl enable anonyfiles-api.service
	@echo "Service démarré et activé au boot."

systemd-stop:
	sudo systemctl stop anonyfiles-api.service
	sudo systemctl disable anonyfiles-api.service
	@echo "Service stoppé et désactivé."

systemd-status:
	sudo systemctl status anonyfiles-api.service

# --- Packaging desktop ---
# Venv dédié au packaging PyInstaller (Python 3.11+).
# Override PYTHON pour pointer un Python 3.11+ spécifique, ex :
#   make env-pkg PYTHON=/opt/homebrew/bin/python3.12
#
# Choix du modèle spaCy (md par défaut, ~62 Mo ; sm pour ~20 Mo) :
#   make sidecar MODEL=sm
#   make desktop MODEL=sm
PYTHON ?= python3
MODEL  ?= md
SPACY_MODEL_VERSION = 3.8.0
SPACY_MODEL_WHEEL = https://github.com/explosion/spacy-models/releases/download/fr_core_news_$(MODEL)-$(SPACY_MODEL_VERSION)/fr_core_news_$(MODEL)-$(SPACY_MODEL_VERSION)-py3-none-any.whl

env-pkg:
	@echo "🔧 Création de env-pkg pour le packaging (PyInstaller + API)..."
	$(PYTHON) -m venv env-pkg
	env-pkg/bin/pip install --upgrade pip setuptools wheel
	env-pkg/bin/pip install -e ".[packaging]"
	env-pkg/bin/pip install $(SPACY_MODEL_WHEEL)

sidecar: env-pkg
	@echo "📦 Build du sidecar anonyfiles-api (modèle=$(MODEL)) via PyInstaller..."
	env-pkg/bin/python packaging/sidecar/build_sidecar.py --clean --model $(MODEL)

desktop: sidecar
	@echo "🖥️  Build du bundle desktop Tauri (embarque le sidecar)..."
	cd anonyfiles_gui && npm install && npm run tauri build
	@if [ "$$(uname)" = "Darwin" ]; then \
		APP=anonyfiles_gui/src-tauri/target/release/bundle/macos/anonyfiles_gui.app; \
		if [ -d "$$APP" ]; then \
			echo "🔏 Nettoyage .DS_Store + re-signature ad-hoc du .app..."; \
			find "$$APP" -name '.DS_Store' -delete; \
			codesign --force --deep --sign - "$$APP"; \
			spctl --assess --type execute --verbose "$$APP" || true; \
		fi; \
	fi