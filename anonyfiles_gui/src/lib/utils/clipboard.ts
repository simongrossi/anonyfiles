export async function copyTextToClipboard(text: string): Promise<boolean> {
  // @ts-ignore
  const isTauri = !!window.__TAURI__;
  if (isTauri) {
    try {
      const { writeText } = await import('@tauri-apps/api/clipboard');
      await writeText(text);
      return true;
    } catch (err) {
      console.error("Erreur Tauri clipboard", err);
      return false;
    }
  } else if (navigator && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error("Erreur navigator.clipboard", err);
      return false;
    }
  } else {
    console.error("Aucune méthode de copie disponible");
    return false;
  }
}
