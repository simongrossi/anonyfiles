/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  // Ajoute ici toutes tes autres variables d'environnement VITE_
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}