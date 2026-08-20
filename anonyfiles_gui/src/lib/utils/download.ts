// #anonyfiles/anonyfiles_gui/src/lib/utils/download.ts
//
// Enregistrement d'un fichier depuis le front.
//
// Dans un navigateur classique, un <a download> + blob URL suffit. Dans la
// webview Tauri (WKWebView sur macOS, WebKitGTK sur Linux) ce mécanisme est
// silencieusement ignoré : le clic ne déclenche aucun téléchargement et
// l'utilisateur n'a aucun retour. On passe donc par la boîte de dialogue
// native (plugin-dialog) + écriture disque (plugin-fs) quand on tourne dans
// Tauri.
import { debugError } from './api';
import { isTauri } from './runtime';

export type SaveOutcome = 'saved' | 'cancelled' | 'error';

function extensionOf(fileName: string): string {
  const dot = fileName.lastIndexOf('.');
  return dot > 0 ? fileName.slice(dot + 1).toLowerCase() : '';
}

async function toUint8Array(data: BlobPart): Promise<Uint8Array> {
  if (data instanceof Uint8Array) return data;
  if (data instanceof ArrayBuffer) return new Uint8Array(data);
  const buffer = await new Blob([data]).arrayBuffer();
  return new Uint8Array(buffer);
}

function saveViaAnchor(data: BlobPart, fileName: string, mime: string): SaveOutcome {
  try {
    const blob = data instanceof Blob ? data : new Blob([data], { type: mime });
    const link = document.createElement('a');
    link.download = fileName;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      link.remove();
    }, 200);
    return 'saved';
  } catch (err) {
    debugError('Erreur export navigateur', err);
    return 'error';
  }
}

/**
 * Propose à l'utilisateur d'enregistrer `data` sous le nom `fileName`.
 *
 * Renvoie `'cancelled'` si la boîte de dialogue native a été fermée sans
 * choisir de destination, ce qui n'est pas une erreur.
 */
export async function saveFile(
  data: BlobPart,
  fileName: string,
  mime = 'application/octet-stream'
): Promise<SaveOutcome> {
  if (!isTauri()) {
    return saveViaAnchor(data, fileName, mime);
  }

  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const ext = extensionOf(fileName);
    const targetPath = await save({
      defaultPath: fileName,
      filters: ext ? [{ name: ext.toUpperCase(), extensions: [ext] }] : undefined,
    });
    if (!targetPath) return 'cancelled';

    const { writeFile } = await import('@tauri-apps/plugin-fs');
    await writeFile(targetPath as string, await toUint8Array(data));
    return 'saved';
  } catch (err) {
    debugError('Erreur export Tauri', err);
    return 'error';
  }
}

export function saveTextFile(
  text: string,
  fileName: string,
  mime = 'text/plain;charset=utf-8'
): Promise<SaveOutcome> {
  return saveFile(new Blob([text], { type: mime }), fileName, mime);
}

/**
 * Construit un nom de fichier de sortie à partir du nom d'origine :
 * `contrat.docx` + `_anonymise` -> `contrat_anonymise.docx`.
 */
export function suffixedFileName(
  originalName: string,
  suffix: string,
  fallback: string
): string {
  const name = (originalName || '').trim();
  if (!name) return fallback;
  const dot = name.lastIndexOf('.');
  if (dot <= 0) return `${name}${suffix}`;
  return `${name.slice(0, dot)}${suffix}${name.slice(dot)}`;
}
