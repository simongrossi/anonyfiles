# Étape 1 : Construction de l'application Svelte/Vite
FROM node:20-alpine as build

WORKDIR /app

# Copie des fichiers de dépendances
COPY package.json package-lock.json* ./

# Installation des dépendances
RUN npm install

# Copie du reste du code source du GUI
COPY . .

# Construction pour la production (exécute 'node copy-presets.js && vite build' selon votre package.json)
RUN npm run build

# Étape 2 : Serveur Web pour distribuer les fichiers statiques
FROM nginx:alpine

# Copie des fichiers construits depuis l'étape précédente vers le dossier de Nginx
# Note : Vite place généralement la sortie dans 'dist' par défaut
COPY --from=build /app/dist /usr/share/nginx/html

# Expose le port 80 pour le trafic web
# Copie de la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
