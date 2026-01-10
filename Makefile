# ====================================================================================
# Anonyfiles Makefile
# ====================================================================================
# Variables pour la configuration des environnements et des exécutables.
# La variable PYTHON_INTERP peut être surchargée (ex: make PYTHON_INTERP=python3.11)
PYTHON_INTERP ?= python3

CLI_VENV := env-cli
API_VENV := env-api
GUI_VENV := env-gui
CLI_PYTHON := $(CLI_VENV)/bin/python
API_PYTHON := $(API_VENV)/bin/python
CLI_PIP := $(CLI_VENV)/bin/pip
API_PIP := $(API_VENV)/bin/pip
GUI_PIP := $(GUI_VENV)/bin/pip

# Fichiers "tampons" pour suivre l'état des installations et éviter les réinstallations inutiles.
CLI_DEPS_STAMP := $(CLI_VENV)/.deps_installed
API_DEPS_STAMP := $(API_VENV)/.deps_installed
GUI_DEPS_STAMP := $(GUI_VENV)/.deps_installed
NPM_DEPS_STAMP := anonyfiles_gui/node_modules

.DEFAULT_GOAL := help

.PHONY: help setup setup-cli setup-api setup-gui reinstall-cli git-config commit venvs compile-deps spacy-models help-cli api gui tui test lint format docs clean test-api systemd-install systemd-start systemd-stop systemd-status

help: ## ✨ Affiche cette aide
	@echo "Anonyfiles Makefile"
	@echo "-------------------"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# --- Targets de Setup Modulaires ---
setup: setup-cli setup-api setup-gui ## 🚀 Installe tout le projet (CLI, API, GUI).
	@echo "✅ Tous les environnements sont prêts."

setup-cli: $(CLI_DEPS_STAMP) spacy-models ## 🚀 Installe uniquement l'environnement pour la CLI et la TUI.
	@echo "✅ Environnement CLI/TUI prêt."

setup-api: $(API_DEPS_STAMP) ## 🚀 Installe uniquement l'environnement pour l'API.
	@echo "✅ Environnement API prêt."

setup-gui: $(GUI_DEPS_STAMP) $(NPM_DEPS_STAMP) ## 🚀 Installe uniquement l'environnement pour la GUI.
	@echo "✅ Environnement GUI prêt."

reinstall-cli: ## 🔄 Force la réinstallation de l'environnement CLI/TUI.
	@echo "🧹 Nettoyage de l'environnement CLI..."
	rm -rf $(CLI_VENV)
	@echo "🚀 Réinstallation de l'environnement CLI/TUI..."
	$(MAKE) setup-cli

git-config: ## ⚙️ Configure git (template + hooks)
	git config commit.template .gitmessage
	git config core.hooksPath .githooks
	chmod +x .githooks/commit-msg
	@echo "✅ Git configuré : Template .gitmessage et Hooks dans .githooks/"

commit: setup-cli ## 🖊️  Crée un commit standardisé avec l'assistant interactif
	$(CLI_VENV)/bin/cz commit

venvs: $(CLI_VENV)/bin/activate $(API_VENV)/bin/activate $(GUI_VENV)/bin/activate ## 🔧 Crée les environnements virtuels Python
	@echo "✅ Environnements virtuels créés ou déjà existants."

# Règle pour créer un environnement virtuel s'il n'existe pas
$(CLI_VENV)/bin/activate:
	$(PYTHON_INTERP) -m venv $(CLI_VENV)

$(API_VENV)/bin/activate:
	$(PYTHON_INTERP) -m venv $(API_VENV)

$(GUI_VENV)/bin/activate:
	$(PYTHON_INTERP) -m venv $(GUI_VENV)

$(CLI_DEPS_STAMP): $(CLI_VENV)/bin/activate requirements.txt requirements-test.txt Makefile
	@echo "📦 Installation des dépendances pour anonyfiles_cli (prod + test)..."
	$(CLI_PIP) install --upgrade pip setuptools wheel
	$(CLI_PIP) install -r requirements.txt
	$(CLI_PIP) install -r requirements-test.txt
	$(CLI_PIP) install black # Recommandé dans CONTRIBUTING.md
	touch $(CLI_DEPS_STAMP)

$(API_DEPS_STAMP): $(API_VENV)/bin/activate requirements.txt Makefile
	@echo "📦 Installation des dépendances pour anonyfiles_api..."
	$(API_PIP) install --upgrade pip setuptools wheel
	$(API_PIP) install -r requirements.txt
	touch $(API_DEPS_STAMP)

$(GUI_DEPS_STAMP): $(GUI_VENV)/bin/activate Makefile
	@echo "📦 Installation des dépendances Python pour anonyfiles_gui (si requirements.txt présent)..."
	if [ -f anonyfiles_gui/requirements.txt ]; then \
		$(GUI_PIP) install --upgrade pip setuptools wheel && \
		$(GUI_PIP) install -r anonyfiles_gui/requirements.txt; \
	fi
	touch $(GUI_DEPS_STAMP)

$(NPM_DEPS_STAMP): anonyfiles_gui/package.json Makefile
	@echo "📦 Installation des modules npm pour anonyfiles_gui..."
	@if ! command -v npm >/dev/null 2>&1; then \
		echo "🧰 AVERTISSEMENT: 'npm' n'est pas installé. L'installation des dépendances GUI est ignorée."; \
		echo "Pour l'installer sur Debian/Ubuntu: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"; \
	else \
		cd anonyfiles_gui && npm install; \
	fi

compile-deps: $(CLI_VENV)/bin/activate ## 🔄 Génère les fichiers requirements.txt à partir des fichiers .in
	@echo "📦 Installation de pip-tools dans l'environnement CLI..."
	$(CLI_PIP) install --quiet pip-tools
	@echo "🔄 Compilation de requirements.txt..."
	$(CLI_PYTHON) -m piptools compile -q requirements.in -o requirements.txt
	@echo "🔄 Compilation de requirements-test.txt..."
	$(CLI_PYTHON) -m piptools compile -q requirements-test.in -o requirements-test.txt
	@echo "✅ Fichiers de dépendances mis à jour."

spacy-models: $(CLI_VENV)/bin/activate ## 📚 Télécharge les modèles spaCy nécessaires
	@echo "📦 Téléchargement des modèles spaCy (fr_core_news_md et xx_ent_wiki_sm)..."
	$(CLI_PYTHON) -m spacy download fr_core_news_md
	$(CLI_PYTHON) -m spacy download xx_ent_wiki_sm

help-cli: setup-cli ## ▶️ Affiche l'aide de la commande CLI
	$(CLI_VENV)/bin/anonyfiles-cli --help

api: ## 🚀 Lancement de l'API FastAPI en mode développement
	$(API_VENV)/bin/uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port 8000 --reload

gui: ## 🖥️  Lance l'interface graphique en mode développement
	cd anonyfiles_gui && npm run tauri dev

test-api: ## 🔗 Envoie une requête de test à l'API
	@echo "🔗 Envoi du fichier vers $${API_URL:-http://localhost:8000}"
	curl -X POST $${API_URL:-http://localhost:8000}/api/anonymize/ \
		-F "file=@tests/sample.txt;type=text/plain" \
		-F 'config_options={"anonymizePersons":true,"anonymizeLocations":true,"anonyfilesOrgs":true,"anonymizeEmails":true,"anonymizeDates":true,"custom_replacement_rules":[]}' \
		-F "file_type=txt"

tui: setup-cli ## 🖼️  Lance l'interface TUI interactive pour les logs
	@# Vérification que la dépendance 'textual' est bien installée avant de lancer.
	@if ! $(CLI_PIP) show textual > /dev/null 2>&1; then \
		echo ""; \
		echo "❌ Erreur: La dépendance 'textual' est introuvable dans l'environnement '$(CLI_VENV)'."; \
		echo "   L'environnement est probablement désynchronisé. Pour corriger cela, lancez :"; \
		echo "   make reinstall-cli"; \
		exit 1; \
	fi
	$(CLI_VENV)/bin/anonyfiles-cli logs interactive

test: setup-cli ## 🔬 Lance la suite de tests avec pytest
	@echo "🔬 Lancement des tests..."
	$(CLI_PYTHON) -m pytest

lint: $(CLI_DEPS_STAMP) ## 🎨 Vérifie le formatage du code avec Black
	@echo "🎨 Vérification du formatage du code avec Black..."
	$(CLI_PYTHON) -m black . --check

format: $(CLI_DEPS_STAMP) ## 🎨 Formate le code avec Black
	@echo "🎨 Formatage du code avec Black..."
	$(CLI_PYTHON) -m black .

docs: $(CLI_DEPS_STAMP) ## 📚 Génère la documentation du code avec Sphinx
	@echo "📚 Génération de la documentation HTML..."
	$(CLI_PYTHON) -m sphinx.build -b html docs docs/_build/html
	@echo "✅ Documentation disponible dans docs/_build/html/index.html"

clean: ## 🧹 Supprime les environnements virtuels et les caches Python
	rm -rf $(CLI_VENV) $(API_VENV) $(GUI_VENV) anonyfiles_gui/node_modules docs/_build
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

# --- Systemd Targets ---
systemd-install: ## 🛡️ Installe le service systemd pour l'API
	sudo cp deploy/anonyfiles-api.service /etc/systemd/system/anonyfiles-api.service
	sudo systemctl daemon-reload
	@echo "Service systemd installé. Tu peux maintenant faire 'make systemd-start'"

systemd-start: ## 🟢 Démarre et active le service systemd
	sudo systemctl start anonyfiles-api.service
	sudo systemctl enable anonyfiles-api.service
	@echo "Service démarré et activé au boot."

systemd-stop: ## 🔴 Stoppe et désactive le service systemd
	sudo systemctl stop anonyfiles-api.service
	sudo systemctl disable anonyfiles-api.service
	@echo "Service stoppé et désactivé."

systemd-status: ## ❓ Affiche le statut du service systemd
	sudo systemctl status anonyfiles-api.service