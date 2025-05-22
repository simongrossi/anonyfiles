# Makefile racine du projet Anonyfiles

.PHONY: setup cli api gui clean

# Crée tous les environnements virtuels
setup:
	@echo "🔧 Setup complet des environnements"
	bash setup_envs.sh

# Lance le moteur CLI
cli:
	source env-cli/bin/activate && python anonyfiles-cli/main.py

# Lance l'API FastAPI
api:
	source env-api/bin/activate && uvicorn anonyfiles_api.api:app --host 127.0.0.1 --port 8000 --reload

# Lance la GUI (Svelte + Tauri)
gui:
	cd anonyfiles-gui && npm run tauri dev

# Supprime les environnements virtuels
clean:
	rm -rf env-cli env-api env-gui
