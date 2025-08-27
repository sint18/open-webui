<script lang="ts">
  export let lines = 3;
</script>

<div class="p-4 bg-white dark:bg-gray-900 rounded-lg shadow animate-pulse space-y-2">
  {#each Array(lines) as _}
    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
  {/each}
</div>
