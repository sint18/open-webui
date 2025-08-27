<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  export let start: string = '';
  export let end: string = '';
  const dispatch = createEventDispatcher<{ change: { start: string; end: string } }>();

  $: dispatch('change', { start, end });
</script>

<div class="flex items-center gap-2">
  <input type="date" bind:value={start} class="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100" />
  <span class="text-gray-500 dark:text-gray-400">to</span>
  <input type="date" bind:value={end} class="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100" />
</div>
