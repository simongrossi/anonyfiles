# Makefile racine du projet Anonyfiles

.PHONY: setup cli api gui clean build-gui deploy export-env check-env

# Vérifie les versions de Python, pip et Node
check-env:
	@echo "🔍 Vérification des versions d'environnement"
	@python3 --version
	@pip --version
	@node --version
	@npm --version

# Crée tous les environnements virtuels
setup: check-env
	@echo "🔧 Setup complet des environnements"
	bash setup_envs.sh

# Lance le moteur CLI
cli:
	@echo "🚀 Lancement de la CLI"
	cd anonyfiles_cli && source venv/bin/activate && python main.py

# Lance l'API FastAPI
api:
	@echo "🚀 Lancement de l’API FastAPI"
	cd anonyfiles_api && source venv/bin/activate && PYTHONPATH=.. uvicorn anonyfiles_api.api:app --host 127.0.0.1 --port 8000

# Lance la GUI (Svelte + Tauri)
gui:
	@echo "🎨 Lancement de la GUI Tauri"
	cd anonyfiles_gui && npm run tauri dev

# Construit la GUI en mode production
build-gui:
	@echo "📦 Build de la GUI"
	cd anonyfiles_gui && npm install && npm run build

# Déploie les fichiers de la GUI dans /var/www/html
deploy: build-gui
	@echo "🚀 Déploiement de la GUI dans /var/www/html"
	sudo rm -rf /var/www/html/*
	cp -r anonyfiles_gui/dist/* /var/www/html/
	@echo "🔄 Redémarrage de l'API (si systemd est en place)"
	sudo systemctl restart anonyfiles-api || true

# Supprime les environnements virtuels
clean:
	@echo "🧹 Suppression des environnements"
	rm -rf anonyfiles_cli/venv anonyfiles_api/venv anonyfiles_gui/venv

# Exporte les versions gelées de toutes les dépendances Python
export-env:
	@echo "📋 Export des dépendances dans requirements.lock.txt"
	cd anonyfiles_api && source venv/bin/activate && pip freeze > ../../requirements.lock.txt && deactivate