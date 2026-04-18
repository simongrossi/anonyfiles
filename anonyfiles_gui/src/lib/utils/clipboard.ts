import { debugError } from './api';
import { isTauri } from './runtime';

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (isTauri()) {
    try {
      const { writeText } = await import('@tauri-apps/plugin-clipboard-manager');
      await writeText(text);
      return true;
    } catch (err) {
      debugError("Erreur Tauri clipboard", err);
      return false;
    }
  } else if (navigator && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      debugError("Erreur navigator.clipboard", err);
      return false;
    }
  } else {
    debugError("Aucune méthode de copie disponible");
    return false;
  }
}
