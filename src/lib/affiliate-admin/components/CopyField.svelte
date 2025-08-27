<script lang="ts">
  import { toast } from 'svelte-sonner';
  export let value: string = '';
  export let label: string = '';
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      toast.success('Copied to clipboard');
    } catch (e) {
      toast.error('Failed to copy');
    }
  };
</script>

<div class="w-full">
  {#if label}
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
  {/if}
  <div class="flex items-center gap-2">
    <input class="flex-1 px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100" bind:value readonly />
    <button type="button" on:click={copy} class="px-3 py-2 rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium">Copy</button>
  </div>
</div>
