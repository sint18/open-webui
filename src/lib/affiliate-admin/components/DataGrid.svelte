<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createGrid, type ColDef, type GridApi, type GridOptions } from 'ag-grid-community';
	import 'ag-grid-community/styles/ag-grid.css';
	import 'ag-grid-community/styles/ag-theme-alpine.css';

	export let columnDefs: ColDef[] = [];
	export let rowData: any[] = [];
	export let gridOptions: GridOptions = {};
	export let className = 'ag-theme-alpine';

	let gridDiv: HTMLDivElement;
	let api: GridApi | undefined;
	let grid: GridApi | undefined;

	onMount(() => {
		const options: GridOptions = {
			...gridOptions, columnDefs, rowData, defaultColDef: {
				flex: 1
			},
		};
		grid = createGrid(gridDiv, options);
		api = options.api;
	});

	onDestroy(() => {
		grid?.destroy();
	});

	$: if (api) {
		api.setColumnDefs(columnDefs);
	}

	$: if (api) {
		api.setGridOption('rowData', rowData);
	}

	export const refresh = () => api?.refreshCells();
</script>

<div bind:this={gridDiv} class={className} style="width: 100%; height: 100%;"></div>

