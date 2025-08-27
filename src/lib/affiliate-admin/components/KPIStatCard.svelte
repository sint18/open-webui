<script lang="ts">
  export let title: string = '';
  export let value: string | number = '';
  export let icon: typeof import('svelte').SvelteComponent | null = null;
  export let change: string = '';
  export let changeType: 'increase' | 'decrease' | '' = '';
</script>

<div class="p-4 bg-white dark:bg-gray-900 rounded-lg shadow flex items-center">
  {#if icon}
    <span class="p-3 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 mr-4">
      <svelte:component this={icon} />
    </span>
  {/if}
  <div class="flex-1">
    {#if title}
      <p class="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
    {/if}
    <div class="flex items-baseline">
      <p class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
      {#if change}
        <span class="ml-2 text-xs font-medium {changeType === 'increase' ? 'text-green-600 dark:text-green-400' : changeType === 'decrease' ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}">{change}</span>
      {/if}
    </div>
  </div>
</div>
