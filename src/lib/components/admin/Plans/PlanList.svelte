<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { DataGrid, EmptyState } from '$lib/affiliate-admin/components';
	import type { ColDef, GridOptions } from 'ag-grid-community';
	import PlanModal from './PlanModal.svelte';
	import { getPlans, deletePlan } from '$lib/apis/plans';
	import type { Plan } from '$lib/types/plans';
	import { toast } from 'svelte-sonner';

	let plans: Plan[] = [];
	let loading = false;
	let showModal = false;
	let currentPlan: Plan | null = null;
	const i18n = getContext('i18n');

	onMount(async () => {
		await loadPlans();
	});

	async function loadPlans() {
		loading = true;
		try {
			plans = await getPlans(localStorage.token);
		} catch (e) {
			toast.error(`${e}`);
		} finally {
			loading = false;
		}
	}

	function openCreate() {
		currentPlan = null;
		showModal = true;
	}

	function openEdit(plan: Plan) {
		currentPlan = plan;
		showModal = true;
	}

	async function handleDelete(plan: Plan) {
		if (!confirm('Delete plan?')) return;
		try {
			await deletePlan(localStorage.token, plan.id);
			plans = plans.filter((p) => p.id !== plan.id);
		} catch (e) {
			toast.error(`${e}`);
		}
	}

	function actionCellRenderer(params: any) {
		const eDiv = document.createElement('div');

		const editBtn = document.createElement('button');
		editBtn.textContent = 'Edit';
		editBtn.className = 'text-blue-600 hover:underline mr-2';
		editBtn.addEventListener('click', () => openEdit(params.data));
		eDiv.appendChild(editBtn);

		const delBtn = document.createElement('button');
		delBtn.textContent = 'Delete';
		delBtn.className = 'text-red-600 hover:underline';
		delBtn.addEventListener('click', () => handleDelete(params.data));
		eDiv.appendChild(delBtn);

		return eDiv;
	}

	function handleSaved(event: CustomEvent<Plan>) {
		const saved = event.detail;
		const idx = plans.findIndex((p) => p.id === saved.id);
		if (idx >= 0) {
			plans[idx] = saved;
			plans = [...plans];
		} else {
			plans = [...plans, saved];
		}
	}

	const columnDefs: ColDef[] = [
		{ headerName: 'ID', field: 'id', sortable: true },
		{ headerName: 'Name', field: 'name', sortable: true },
		{ headerName: 'Type', field: 'plan_type', sortable: true },
		{ headerName: 'Price', field: 'price', sortable: true },
		{ headerName: 'Credits', field: 'credits', sortable: true },
		{ headerName: 'Image Credits', field: 'image_credits', sortable: true },
		{ headerName: 'Video Credits', field: 'video_credits', sortable: true },
		{ headerName: 'Features', field: 'features', sortable: true, cellRenderer: (params) => JSON.stringify(params.data.features, null, 2) },
		{ headerName: 'Description', field: 'description', sortable: true },
		{ headerName: 'Active', field: 'is_active', sortable: true },
		{ headerName: 'Actions', cellRenderer: actionCellRenderer, sortable: false, filter: false }
	];

	const gridOptions: GridOptions = { domLayout: 'autoHeight' };
</script>

<div class="space-y-4 text-gray-800 dark:text-gray-200">
	<div class="flex justify-between items-center">
		<h2 class="text-xl font-semibold">Plans</h2>
		<button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={openCreate}>Add Plan</button>
	</div>

	{#if loading}
		<p>Loading...</p>
	{:else if plans.length === 0}
		<EmptyState title={$i18n.t('No applications')} />
	{:else}
		<DataGrid {columnDefs} rowData={plans} {gridOptions} />
	{/if}
</div>

<PlanModal bind:show={showModal} plan={currentPlan} on:saved={handleSaved} />

