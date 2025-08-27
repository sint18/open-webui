<script lang="ts">
  export let columns = 3;
  export let rows = 5;
</script>

<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-800 animate-pulse">
  <thead class="bg-gray-50 dark:bg-gray-900">
    <tr>
      {#each Array(columns) as _, i}
        <th class="px-4 py-2">
          <div class="h-3 w-1/2 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </th>
      {/each}
    </tr>
  </thead>
  <tbody class="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
    {#each Array(rows) as _, r}
      <tr>
        {#each Array(columns) as _}
          <td class="px-4 py-2">
            <div class="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
          </td>
        {/each}
      </tr>
    {/each}
  </tbody>
</table>
