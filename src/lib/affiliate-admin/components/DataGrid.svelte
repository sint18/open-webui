<script lang="ts">
  export interface Column {
    key: string;
    label: string;
    class?: string;
  }
  export let columns: Column[] = [];
  export let rows: any[] = [];
</script>

<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
  <thead class="bg-gray-50 dark:bg-gray-900">
    <tr>
      {#each columns as column}
        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider {column.class ?? ''}">
          {column.label}
        </th>
      {/each}
    </tr>
  </thead>
  <tbody class="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
    {#if rows.length === 0}
      <tr>
        <td class="px-4 py-4 text-center text-sm text-gray-500 dark:text-gray-400" colspan={columns.length}>
          <slot name="empty">No data</slot>
        </td>
      </tr>
    {:else}
      {#each rows as row}
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-900">
          {#each columns as column}
            <td class="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
              <slot name={column.key} {row}>{row[column.key]}</slot>
            </td>
          {/each}
        </tr>
      {/each}
    {/if}
  </tbody>
</table>
