<script lang="ts">
  export let status: 'success' | 'warning' | 'error' | 'info' | 'default' = 'default';
  export let label: string = '';

  const classes = {
    success: 'bg-green-100 text-green-800 dark:bg-green-800/20 dark:text-green-300',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800/20 dark:text-yellow-300',
    error: 'bg-red-100 text-red-800 dark:bg-red-800/20 dark:text-red-300',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-800/20 dark:text-blue-300',
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-800/20 dark:text-gray-300'
  } as const;
</script>

<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {classes[status]}">{label}</span>
