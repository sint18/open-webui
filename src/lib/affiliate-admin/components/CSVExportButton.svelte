<script lang="ts">
  import { toast } from 'svelte-sonner';
  export let data: Record<string, any>[] = [];
  export let filename: string = 'export.csv';

  const exportCSV = () => {
    if (!data || data.length === 0) {
      toast.error('No data to export');
      return;
    }
    const keys = Object.keys(data[0]);
    const rows = data.map(row => keys.map(k => JSON.stringify(row[k] ?? '')).join(','));
    const csvContent = [keys.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('CSV downloaded');
  };
</script>

<button type="button" on:click={exportCSV} class="px-3 py-2 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-sm font-medium">
  Export CSV
</button>
