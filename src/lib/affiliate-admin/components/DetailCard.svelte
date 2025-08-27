<script lang="ts">
  export let title: string = '';
  export let items: { label: string; value: any }[] = [];
</script>

<div class="rounded-lg bg-white dark:bg-gray-900 shadow p-4">
  {#if title}
    <h3 class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">{title}</h3>
  {/if}
  <div class="space-y-2">
    {#each items as item}
      <div class="flex justify-between text-sm">
        <span class="text-gray-500 dark:text-gray-400">{item.label}</span>
        <span class="text-gray-900 dark:text-gray-100">
<!--          <slot name={item.label} {item}>{item.value}</slot>-->
        </span>
      </div>
    {/each}
    <slot />
  </div>
</div>
