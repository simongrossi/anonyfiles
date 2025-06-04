// anonyfiles/anonyfiles_gui/copy-presets.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dossier source désormais dans anonyfiles_gui/wordlist_presets
const sourceDir = path.resolve(__dirname, './wordlist_presets');
const destDir = path.resolve(__dirname, './public/presets');

if (!fs.existsSync(sourceDir)) {
  console.error('❌ Le dossier source "anonyfiles_gui/wordlist_presets" est introuvable.');
  process.exit(1);
}

if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
}

const files = fs.readdirSync(sourceDir).filter(file => file.endsWith('.json'));

files.forEach(file => {
  const src = path.join(sourceDir, file);
  const dest = path.join(destDir, file);
  fs.copyFileSync(src, dest);
  console.log(`✅ Copié : ${file}`);
});

console.log(`📁 Tous les fichiers JSON ont été copiés dans public/presets`);
