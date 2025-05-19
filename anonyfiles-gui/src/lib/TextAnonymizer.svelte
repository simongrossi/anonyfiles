<script>
	import { invoke } from '@tauri-apps/api/tauri';

	export let fileContent = '';
	let inputText = '';
	let outputText = '';
	let isLoading = false;

	// --- Nouvelle variable d'état pour l'option PER ---
	let anonymizePersons = true; // Option activée par défaut
	// ---------------------------------------------

	async function anonymize() {
		if (!inputText.trim()) return;
		isLoading = true;
		outputText = ''; // Clear previous output

		// --- Construire l'objet de configuration ---
		// Nous allons passer un objet 'config' au backend
		const config = {
			// Inclure l'état de l'option pour les personnes
			anonymizePersons: anonymizePersons
			// On pourra ajouter d'autres options ici plus tard
		};
		// ------------------------------------------

		try {
			// Appel vers Rust -> Python via la commande enregistrée dans main.rs
			// --- Passer l'objet de configuration au backend comme deuxième argument ---
			// Tauri permet de passer des objets JSON dans les arguments des commandes
			const result = await invoke('anonymize_text', { input: inputText, config: config });
			// -----------------------------------------------------------------------
			outputText = result;
		} catch (error) {
			// La structure de l'erreur peut varier, afficher l'objet entier pour débogage
			console.error("Anonymization Error:", error);
			outputText = 'Erreur lors de l’anonymisation : ' + JSON.stringify(error, null, 2);
		} finally {
			isLoading = false;
		}
	}

	// Synchronise le champ si un fichier est glissé/déposé
	$: if (fileContent) {
		inputText = fileContent;
		outputText = '';
	}
</script>

<div class="anonymizer">
	<textarea
		bind:value={inputText}
		placeholder="Texte à anonymiser"
		rows="6"
	></textarea>

	<div class="options-row">
		<label for="anonymizePersons">Anonymiser les personnes (PER)</label>
		<input type="checkbox" id="anonymizePersons" bind:checked={anonymizePersons} />
	</div>
	<button on:click={anonymize} disabled={isLoading}>
		{isLoading ? 'Traitement en cours…' : 'Anonymiser'}
	</button>

	<textarea
		bind:value={outputText}
		placeholder="Texte anonymisé"
		rows="6"
		readonly
	></textarea>
</div>

<style>
	.anonymizer {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	textarea {
		width: 100%;
		padding: 1rem;
		border-radius: 8px;
		border: 1px solid #444;
		font-size: 1rem;
		background-color: #fff;
		color: #000;
		resize: vertical;
		box-sizing: border-box;
	}

	textarea[readonly] {
		background-color: #f8f8f8;
	}

	button {
		padding: 0.75rem;
		font-size: 1rem;
		border-radius: 8px;
		background-color: #646cff;
		color: white;
		border: none;
		cursor: pointer;
		transition: background-color 0.3s ease;
	}

	button:disabled {
		background-color: #999;
		cursor: wait;
	}

	button:hover:enabled {
		background-color: #535bf2;
	}

	/* --- Style pour aligner label et checkbox --- */
	.options-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #f0f0f0; /* Assurez-vous que le label est visible avec le fond sombre */
	}
	/* ------------------------------------------- */
</style>