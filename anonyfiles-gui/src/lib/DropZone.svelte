<script>
  export let onDrop = () => {};
  export let label = "Déposez un fichier ici ou cliquez pour parcourir";
  export let accept = "";
  let fileInput;

  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer?.files?.length > 0) {
      onDrop(event.dataTransfer.files);
    }
  }

  function handleClick() {
    fileInput.click();
  }

  function handleFileChange(event) {
    if (event.target?.files?.length > 0) {
      onDrop(event.target.files);
    }
  }

  function handleKeydown(event) {
    if (event.key === "Enter" || event.key === " ") {
      handleClick();
    }
  }
</script>

<button
  type="button"
  class="border-2 border-dashed rounded-xl border-zinc-300 transition-all bg-white dark:bg-zinc-950 text-zinc-800 dark:text-zinc-100 text-center px-4 py-6 mb-5 cursor-pointer select-none relative
         hover:border-blue-400 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
  on:dragover|preventDefault
  on:drop={handleDrop}
  on:click={handleClick}
  on:keydown={handleKeydown}
  aria-label={label}
  tabindex="0"
>
  <span class="block pointer-events-none select-none">{label}</span>
  <input
    type="file"
    bind:this={fileInput}
    accept={accept}
    class="hidden"
    on:change={handleFileChange}
    tabindex="-1"
  />
</button>
