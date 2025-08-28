<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import { DataGrid, ConfirmDialog, EmptyState, DataGridSkeleton } from '$lib/affiliate-admin/components';
  import Modal from '$lib/components/common/Modal.svelte';
  import { applicationsTable } from '$lib/affiliate-admin/stores';
  import { listApplications, approveApplication, rejectApplication, reviewApplicationFlags } from '$lib/affiliate-admin/api';
  import type { Application, ApplicationApproveForm } from '$lib/affiliate-admin/types';
  import type { ColDef } from 'ag-grid-community';
  import dayjs from 'dayjs';

  const i18n = getContext('i18n');

  let loading = false;
  let applications: Application[] = [];
  let currentApp: Application | null = null;
  let showApprove = false;
  let showReject = false;
  let showFlags = false;

  let approveForm: ApplicationApproveForm = { link_code: '', link_url: '' };
  let rejectNote = '';

  const fetchApps = async () => {
    loading = true;
    try {
      applications = await listApplications(localStorage.token, { page: $applicationsTable.page });
    } finally {
      loading = false;
    }
  };

  onMount(fetchApps);
  $: $applicationsTable.page, fetchApps();

  function openApprove(app: Application) {
    currentApp = app;
    approveForm = { link_code: '', link_url: '' };
    showApprove = true;
  }

  async function submitApprove() {
    if (!currentApp) return;
    await approveApplication(localStorage.token, currentApp.id, approveForm);
    currentApp.status = 'approved';
    showApprove = false;
  }

  function openReject(app: Application) {
    currentApp = app;
    rejectNote = '';
    showReject = true;
  }

  async function submitReject() {
    if (!currentApp) return;
    await rejectApplication(localStorage.token, currentApp.id, { note: rejectNote });
    currentApp.status = 'rejected';
    showReject = false;
  }

  function openFlags(app: Application) {
    currentApp = app;
    showFlags = true;
  }

  async function confirmFlags() {
    if (!currentApp) return;
    await reviewApplicationFlags(localStorage.token, currentApp.id);
    currentApp.fraud_flags = [];
    showFlags = false;
  }

  function actionCellRenderer(params: any) {
    const eDiv = document.createElement('div');
    if (params.data.status === 'pending') {
      const approveBtn = document.createElement('button');
      approveBtn.textContent = 'Approve';
      approveBtn.className = 'text-blue-600 hover:underline mr-2';
      approveBtn.addEventListener('click', () => openApprove(params.data));
      eDiv.appendChild(approveBtn);

      const rejectBtn = document.createElement('button');
      rejectBtn.textContent = 'Reject';
      rejectBtn.className = 'text-red-600 hover:underline mr-2';
      rejectBtn.addEventListener('click', () => openReject(params.data));
      eDiv.appendChild(rejectBtn);
    }
    if (params.data.fraud_flags && params.data.fraud_flags.length) {
      const flagBtn = document.createElement('button');
      flagBtn.textContent = 'Review Flags';
      flagBtn.className = 'text-yellow-600 hover:underline';
      flagBtn.addEventListener('click', () => openFlags(params.data));
      eDiv.appendChild(flagBtn);
    }
    return eDiv;
  }

  const columnDefs: ColDef[] = [
    { headerName: 'App ID', field: 'id', sortable: true },
    { headerName: 'Partner', field: 'name' },
    { headerName: 'Email', field: 'email' },
    { headerName: 'Status', field: 'status' },
    { headerName: 'Created', field: 'created_at', valueFormatter: (p) => dayjs(p.value * 1000).format('LLL') },
    { headerName: 'Flags', field: 'fraud_flags', valueGetter: (p) => (p.data.fraud_flags || []).join(', ') },
    { headerName: 'Actions', cellRenderer: actionCellRenderer, sortable: false, filter: false }
  ];
  const gridOptions = { domLayout: 'autoHeight' } as const;

  $: if (!showApprove && !showReject && !showFlags) {
    currentApp = null;
  }
</script>

<div class="space-y-4 text-gray-800 dark:text-gray-200">
  <h1 class="text-2xl font-semibold">{$i18n.t('Applications')}</h1>

  {#if loading}
    <DataGridSkeleton />
  {:else if applications.length === 0}
    <EmptyState title={$i18n.t('No applications')} />
  {:else}
    <DataGrid {columnDefs} rowData={applications} {gridOptions} />
  {/if}
</div>

<Modal bind:show={showApprove} size="sm">
  <div class="p-4 space-y-4 text-gray-800 dark:text-gray-200">
    <h2 class="text-lg font-semibold">{$i18n.t('Approve Application')}</h2>
    <div class="space-y-2">
      <label class="block text-sm">Link Code</label>
      <input class="w-full p-2 border rounded" bind:value={approveForm.link_code} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">Link URL</label>
      <input class="w-full p-2 border rounded" bind:value={approveForm.link_url} />
    </div>
    <div class="flex justify-end gap-2">
      <button class="px-3 py-1 rounded bg-gray-200" on:click={() => (showApprove = false)}>{$i18n.t('Cancel')}</button>
      <button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={submitApprove}>{$i18n.t('Approve')}</button>
    </div>
  </div>
</Modal>

<Modal bind:show={showReject} size="sm">
  <div class="p-4 space-y-4 text-gray-800 dark:text-gray-200">
    <h2 class="text-lg font-semibold">{$i18n.t('Reject Application')}</h2>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Reason')}</label>
      <textarea class="w-full p-2 border rounded" rows="4" bind:value={rejectNote}></textarea>
    </div>
    <div class="flex justify-end gap-2">
      <button class="px-3 py-1 rounded bg-gray-200" on:click={() => (showReject = false)}>{$i18n.t('Cancel')}</button>
      <button class="px-3 py-1 rounded bg-red-600 text-white" on:click={submitReject}>{$i18n.t('Reject')}</button>
    </div>
  </div>
</Modal>

<ConfirmDialog bind:show={showFlags} title={$i18n.t('Clear Flags')} onConfirm={confirmFlags} />
