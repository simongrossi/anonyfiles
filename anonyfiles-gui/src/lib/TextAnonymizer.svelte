<script>
	import { invoke } from '@tauri-apps/api/tauri';

	export let fileContent = '';
	let inputText = '';
	let outputText = '';
	let errorMessage = '';
	let isLoading = false;

	let anonymizePersons = true;

	async function anonymize() {
		if (!inputText.trim()) return;
		isLoading = true;
		outputText = '';
		errorMessage = '';

		const config = {
			anonymizePersons: anonymizePersons
			// Ajoute d'autres options ici si besoin
		};

		try {
			const result = await invoke('anonymize_text', { input: inputText, config });
			outputText = result;
		} catch (error) {
			console.error("Anonymization Error:", error);
			errorMessage = typeof error === 'object' ? JSON.stringify(error, null, 2) : String(error);
		} finally {
			isLoading = false;
		}
	}

	$: if (fileContent) {
		inputText = fileContent;
		outputText = '';
		errorMessage = '';
	}
</script>

<div class="flex flex-col gap-4 max-w-xl mx-auto mt-10 p-4 bg-white rounded-xl shadow-lg">
	<textarea
		class="border border-slate-300 p-3 rounded-lg resize-y min-h-[100px] text-base focus:outline-none focus:ring-2 focus:ring-blue-400"
		bind:value={inputText}
		placeholder="Texte à anonymiser"
		rows="6"
	></textarea>

	<div class="flex items-center gap-2">
		<input type="checkbox" id="anonymizePersons" bind:checked={anonymizePersons}
			class="w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-400" />
		<label for="anonymizePersons" class="select-none text-gray-700 text-base">
			Anonymiser les personnes (PER)
		</label>
	</div>

	<button
		class="px-6 py-3 font-semibold text-white rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 transition disabled:bg-gray-400 disabled:cursor-wait"
		on:click={anonymize} disabled={isLoading}
	>
		{isLoading ? 'Traitement en cours…' : 'Anonymiser'}
	</button>

	{#if outputText}
		<textarea
			class="border border-green-300 bg-green-50 text-green-800 p-3 rounded-lg resize-y min-h-[100px] text-base"
			bind:value={outputText}
			placeholder="Texte anonymisé"
			rows="6"
			readonly
		></textarea>
	{/if}

	{#if errorMessage}
		<div class="border border-red-400 bg-red-50 text-red-800 rounded-lg p-3">
			<strong>Erreur lors de l’anonymisation :</strong>
			<pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
		</div>
	{/if}
</div>
