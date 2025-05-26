import App from './App.svelte'; // Importe le composant App.svelte, qui est la racine de votre application
import './app.css'

// Crée une nouvelle instance de l'application Svelte
const app = new App({
  // 'target' spécifie l'élément HTML où l'application Svelte sera insérée.
  // Nous avons configuré index.html pour avoir une <div id="app"></div>
  target: document.getElementById('app')!, // Le '!' indique à TypeScript que cet élément existera bien
});

// Exporte l'instance de l'application (utile pour les tests ou si d'autres modules l'importent)
export default app;