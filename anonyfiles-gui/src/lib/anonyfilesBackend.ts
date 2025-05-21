// src/lib/anonyfilesBackend.ts

type AnonymizeOptions = {
  file: File;
  config_options: object;
  file_type?: string;
  has_header?: boolean;
};

export async function anonymizeFile({ file, config_options, file_type, has_header }: AnonymizeOptions) {
  const isTauri = typeof window !== 'undefined' && '__TAURI__' in window;

  if (isTauri) {
    // Appel Tauri (mode bureau)
    // Adapte selon la signature de ta commande Rust (invoke)
    return await (window as any).__TAURI__.invoke('anonymize_text', {
      filePath: (file as any).path, // (file.path à adapter selon comment tu passes les fichiers en bureau)
      configOptions: config_options,
      fileType: file_type,
      hasHeader: has_header
    });
  } else {
    // Appel web (FastAPI)
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config_options', JSON.stringify(config_options));
    if (file_type) formData.append('file_type', file_type);
    if (has_header !== undefined) formData.append('has_header', String(has_header));
    // Ajoute ici toute logique spécifique (exclude_entities, etc.)

    const API_URL = import.meta.env.VITE_ANONYFILES_API_URL || '/anonymize/';

    const resp = await fetch(API_URL, {
      method: 'POST',
      body: formData
    });

    if (!resp.ok) throw new Error(await resp.text());
    return await resp.json();
  }
}
