import { mount } from 'svelte';
import App from './App.svelte'; // Composant racine de l'application
import './app.css';

// Svelte 5 : on monte l'application via `mount()` (l'API `new App({...})` de
// Svelte 4 n'existe plus — les composants ne sont plus des classes).
const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
