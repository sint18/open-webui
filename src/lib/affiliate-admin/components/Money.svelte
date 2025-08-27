<script lang="ts">
  export let value: number = 0;
  export let currency: string = 'USD';
  export let minimumFractionDigits = 2;
</script>

<span class="font-medium text-gray-900 dark:text-gray-100">
  {new Intl.NumberFormat(undefined, { style: 'currency', currency, minimumFractionDigits }).format(value)}
</span>
