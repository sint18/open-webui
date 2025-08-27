<script lang="ts">
  export let title: string = 'No data';
  export let description: string = '';
  export let icon: typeof import('svelte').SvelteComponent | null = null;
</script>

<div class="text-center py-10">
  {#if icon}
    <div class="mx-auto mb-4 text-gray-400"><svelte:component this={icon} /></div>
  {/if}
  <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</h3>
  {#if description}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
  {/if}
  <slot />
</div>
