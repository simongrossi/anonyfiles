<script>
	import { invoke } from '@tauri-apps/api/tauri';

	export let fileContent = '';
	let inputText = '';
	let outputText = '';
	let errorMessage = '';
	let isLoading = false;
	let anonymizePersons = true;

	let showToast = false;
	let toastTimeout = null;

	async function anonymize() {
		if (!inputText.trim()) return;
		isLoading = true;
		outputText = '';
		errorMessage = '';

		const config = { anonymizePersons };

		try {
			const result = await invoke('anonymize_text', { input: inputText, config });
			outputText = result;
		} catch (error) {
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

	function copyResult() {
		if (outputText) {
			navigator.clipboard.writeText(outputText);
			showToast = true;
			if (toastTimeout) clearTimeout(toastTimeout);
			toastTimeout = setTimeout(() => {
				showToast = false;
			}, 1600);
		}
	}
</script>

<div class="bg-zinc-900 rounded-xl p-6 shadow-lg flex flex-col gap-4 border border-zinc-700 relative">
	<textarea
		class="border border-zinc-600 bg-zinc-950 text-white p-3 rounded-lg resize-y min-h-[100px] text-base focus:outline-none focus:ring-2 focus:ring-blue-400"
		bind:value={inputText}
		placeholder="Texte à anonymiser"
		rows="6"
	></textarea>

	<div class="flex items-center gap-2">
		<input type="checkbox" id="anonymizePersons" bind:checked={anonymizePersons}
			class="w-5 h-5 text-blue-600 rounded border-zinc-400 focus:ring-blue-400 bg-zinc-950" />
		<label for="anonymizePersons" class="select-none text-zinc-200 text-base">
			Anonymiser les personnes (PER)
		</label>
	</div>

	<button
		class="px-6 py-3 font-semibold text-white rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 transition disabled:bg-gray-400 disabled:cursor-wait mt-2 flex items-center justify-center gap-2"
		on:click={anonymize} disabled={isLoading}
	>
		{#if isLoading}
			<svg class="animate-spin h-5 w-5 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
			</svg>
			Traitement en cours…
		{:else}
			Anonymiser
		{/if}
	</button>

	{#if outputText}
		<div class="border border-green-400 bg-green-100 text-green-800 rounded-lg p-4 flex flex-col gap-2 mt-2 relative">
			<div class="flex items-center gap-2 mb-1">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				<span class="font-bold text-green-700">Texte anonymisé :</span>
			</div>
			<textarea
				class="bg-green-50 text-green-900 p-3 rounded-lg resize-y min-h-[60px] border border-green-300 font-mono"
				readonly
				bind:value={outputText}
				rows="4"
			/>
			<button
				class="self-end px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-xs"
				on:click={copyResult}
				type="button"
			>
				Copier
			</button>
			{#if showToast}
				<div class="absolute right-4 top-2 bg-green-600 text-white text-xs rounded px-3 py-1 shadow-lg animate-fadeInOut z-10 select-none">
					✔️ Copié !
				</div>
			{/if}
		</div>
	{/if}

	{#if errorMessage}
		<div class="border border-red-400 bg-red-950 text-red-200 rounded-lg p-3 mt-2">
			<strong>Erreur lors de l’anonymisation :</strong>
			<pre class="whitespace-pre-wrap text-xs">{errorMessage}</pre>
		</div>
	{/if}
</div>

<style>
	@keyframes fadeInOut {
		0%   { opacity: 0; transform: translateY(-8px);}
		10%  { opacity: 1; transform: translateY(0);}
		90%  { opacity: 1;}
		100% { opacity: 0; transform: translateY(-8px);}
	}
	.animate-fadeInOut {
		animation: fadeInOut 1.6s both;
	}
</style>
