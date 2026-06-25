/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_ANONYFILES_API_URL?: string;
  readonly VITE_ANONYFILES_API_KEY?: string;
  // Ajoute ici toutes tes autres variables d'environnement VITE_
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
