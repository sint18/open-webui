<script lang="ts">
  import { onMount } from 'svelte';
  import { DataGrid } from '$lib/affiliate-admin/components';
  import type { ColDef, GridApi, GridOptions } from 'ag-grid-community';
  import QuotaPolicyModal from './QuotaPolicyModal.svelte';
  import { getQuotaPolicies, deleteQuotaPolicy } from '$lib/apis/quota-policies';
  import { getUserById } from '$lib/apis/users';
  import { getPlans } from '$lib/apis/plans';
  import type { QuotaPolicy } from '$lib/types';
  import type { Plan } from '$lib/types/plans';
  import { toast } from 'svelte-sonner';

  let policies: any[] = [];
  let plans: Plan[] = [];
  let loading = false;
  let showModal = false;
  let currentPolicy: QuotaPolicy | null = null;
  let search = '';
  let gridApi: GridApi | null = null;
  const gridOptions: GridOptions = {
    onGridReady: (p) => (gridApi = p.api)
  };

  $: if (gridApi) {
    gridApi.setGridOption('quickFilterText', search);
  }

  onMount(async () => {
    plans = await getPlans(localStorage.token).catch(() => []);
    await loadPolicies();
  });

  async function loadPolicies() {
    loading = true;
    try {
      const raw: QuotaPolicy[] = await getQuotaPolicies(localStorage.token);
      policies = await Promise.all(
        raw.map(async (p) => {
          let user_email = '';
          if (p.user_id) {
            try {
              const user = await getUserById(localStorage.token, p.user_id);
              user_email = user.email;
            } catch (e) {
              console.error(e);
            }
          }
          const plan = plans.find((pl) => pl.id === p.plan_id);
          return { ...p, user_email, plan_name: plan ? plan.name : '' };
        })
      );
    } catch (e) {
      toast.error(`${e}`);
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    currentPolicy = null;
    showModal = true;
  }

  function openEdit(policy: QuotaPolicy) {
    currentPolicy = policy;
    showModal = true;
  }

  async function handleDelete(policy: QuotaPolicy) {
    if (!confirm('Delete policy?')) return;
    try {
      await deleteQuotaPolicy(localStorage.token, policy.id);
      policies = policies.filter((p) => p.id !== policy.id);
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

  async function handleSaved(event: CustomEvent<QuotaPolicy>) {
    const saved = event.detail;
    const plan = plans.find((pl) => pl.id === saved.plan_id);
    let user_email = '';
    if (saved.user_id) {
      try {
        const user = await getUserById(localStorage.token, saved.user_id);
        user_email = user.email;
      } catch (e) {
        console.error(e);
      }
    }
    const enriched = { ...saved, user_email, plan_name: plan ? plan.name : '' };
    const idx = policies.findIndex((p) => p.id === saved.id);
    if (idx >= 0) {
      policies[idx] = enriched;
      policies = [...policies];
    } else {
      policies = [...policies, enriched];
    }
  }

  const columnDefs: ColDef[] = [
    { headerName: 'ID', field: 'id', sortable: true },
    { headerName: 'User Email', field: 'user_email', sortable: true },
    { headerName: 'User ID', field: 'user_id', sortable: true },
    { headerName: 'Plan Name', field: 'plan_name', sortable: true },
    { headerName: 'Plan ID', field: 'plan_id', sortable: true },
    { headerName: 'Resource', field: 'resource_pattern', sortable: true },
    { headerName: 'Limit', field: 'limit', sortable: true },
    { headerName: 'Window', field: 'window', sortable: true },
    {
      headerName: 'Effective From',
      field: 'effective_from',
      valueFormatter: ({ value }) => (value ? new Date(value * 1000).toLocaleString() : ''),
      sortable: true
    },
    {
      headerName: 'Expires At',
      field: 'expires_at',
      valueFormatter: ({ value }) => (value ? new Date(value * 1000).toLocaleString() : ''),
      sortable: true
    },
    { headerName: 'Actions', cellRenderer: actionCellRenderer, sortable: false, filter: false }
  ];
</script>

  <div class="space-y-4 text-gray-800 dark:text-gray-200">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold">Quota Policies</h2>
      <button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={openCreate}>
        Add Quota Policy
      </button>
    </div>

    <input
      class="p-2 border rounded w-full md:w-1/3"
      placeholder="Search"
      bind:value={search}
    />

    {#if loading}
      <p>Loading...</p>
    {:else if policies.length === 0}
      <p>No quota policies found.</p>
    {:else}
      <DataGrid {columnDefs} rowData={policies} {gridOptions} />
    {/if}
  </div>

<QuotaPolicyModal bind:show={showModal} policy={currentPolicy} on:saved={handleSaved} {plans} />
