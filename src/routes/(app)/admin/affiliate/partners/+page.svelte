<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import { DataGrid, Drawer, ConfirmDialog, EmptyState, DataGridSkeleton } from '$lib/affiliate-admin/components';
  import { searchPartners, getPartner, updatePartner, activatePartner, suspendPartner } from '$lib/affiliate-admin/api';
  import type { Partner, PartnerUpdateForm } from '$lib/affiliate-admin/types';
  import type { ColDef, GridApi, GridOptions } from 'ag-grid-community';

  const i18n = getContext('i18n');

  let loading = false;
  let partners: Partner[] = [];
  let search = '';
  let gridApi: GridApi | null = null;
  const gridOptions: GridOptions = {
    domLayout: 'autoHeight',
    onGridReady: (p) => (gridApi = p.api)
  };

  onMount(async () => {
    loading = true;
    try {
      partners = await searchPartners(localStorage.token);
    } finally {
      loading = false;
    }
  });

  $: if (gridApi) {
    gridApi.setGridOption('quickFilterText', search);
  }

  let showEdit = false;
  let currentPartner: Partner | null = null;
  let editForm: PartnerUpdateForm = { name: '', email: '' };

  async function openEdit(partner: Partner) {
    const detail = await getPartner(localStorage.token, partner.id);
    currentPartner = partner;
    editForm = { name: detail.name, email: detail.email };
    showEdit = true;
  }

  async function submitEdit() {
    if (!currentPartner) return;
    const updated = await updatePartner(localStorage.token, currentPartner.id, editForm);
    partners = partners.map((p) => (p.id === currentPartner!.id ? { ...p, ...updated } : p));
    showEdit = false;
  }

  let showConfirm = false;
  let confirmMessage = '';
  let confirmAction: () => void | Promise<void> = async () => {};

  function confirmStatus(partner: Partner) {
    if (partner.status === 'active') {
      confirmMessage = `${$i18n.t('Suspend')} ${partner.name}?`;
      confirmAction = async () => {
        await suspendPartner(localStorage.token, partner.id);
        partners = partners.map((p) => (p.id === partner.id ? { ...p, status: 'suspended' } : p));
      };
    } else {
      confirmMessage = `${$i18n.t('Activate')} ${partner.name}?`;
      confirmAction = async () => {
        await activatePartner(localStorage.token, partner.id);
        partners = partners.map((p) => (p.id === partner.id ? { ...p, status: 'active' } : p));
      };
    }
    showConfirm = true;
  }

  function actionCellRenderer(params: any) {
    const eDiv = document.createElement('div');
    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.className = 'text-blue-600 hover:underline mr-2';
    editBtn.addEventListener('click', () => openEdit(params.data));
    eDiv.appendChild(editBtn);

    const statusBtn = document.createElement('button');
    if (params.data.status === 'active') {
      statusBtn.textContent = 'Suspend';
      statusBtn.className = 'text-red-600 hover:underline';
    } else {
      statusBtn.textContent = 'Activate';
      statusBtn.className = 'text-green-600 hover:underline';
    }
    statusBtn.addEventListener('click', () => confirmStatus(params.data));
    eDiv.appendChild(statusBtn);
    return eDiv;
  }

  const columnDefs: ColDef[] = [
    { headerName: 'ID', field: 'id', sortable: true },
    { headerName: 'Name', field: 'name', sortable: true },
    { headerName: 'Email', field: 'email', sortable: true },
    { headerName: 'Role', field: 'role' },
    { headerName: 'Status', field: 'status' },
    { headerName: 'Balance', field: 'balance' },
    { headerName: 'Actions', cellRenderer: actionCellRenderer, sortable: false, filter: false }
  ];
</script>

<div class="space-y-4 text-gray-800 dark:text-gray-200">
  <h1 class="text-2xl font-semibold">{$i18n.t('Partners')}</h1>

  <input
    class="p-2 border rounded w-full md:w-1/3"
    placeholder={$i18n.t('Search')}
    bind:value={search}
  />

  {#if loading}
    <DataGridSkeleton />
  {:else if partners.length === 0}
    <EmptyState title={$i18n.t('No partners')} />
  {:else}
    <DataGrid {columnDefs} rowData={partners} {gridOptions} />
  {/if}
</div>

<Drawer bind:show={showEdit} onClose={() => (currentPartner = null)}>
  <div class="p-4 space-y-4">
    <h2 class="text-lg font-semibold">{$i18n.t('Edit Partner')}</h2>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Name')}</label>
      <input class="w-full p-2 border rounded" bind:value={editForm.name} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Email')}</label>
      <input class="w-full p-2 border rounded" bind:value={editForm.email} />
    </div>
    <div class="flex justify-end gap-2">
      <button class="px-3 py-1 rounded bg-gray-200" on:click={() => (showEdit = false)}>{$i18n.t('Cancel')}</button>
      <button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={submitEdit}>{$i18n.t('Save')}</button>
    </div>
  </div>
</Drawer>

<ConfirmDialog bind:show={showConfirm} title={$i18n.t('Confirm')} message={confirmMessage} onConfirm={confirmAction} />
