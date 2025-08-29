<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import { page } from '$app/stores';
  import {
    DataGrid,
    DataGridSkeleton,
    EmptyState,
    ConfirmDialog
  } from '$lib/affiliate-admin/components';
  import Modal from '$lib/components/common/Modal.svelte';
  import {
    getPartner,
    listLinks,
    listCoupons,
    listCommissions,
    listPayouts,
    getPayout,
    updatePartner,
    activatePartner,
    suspendPartner
  } from '$lib/affiliate-admin/api';
  import type {
    PartnerDetail,
    PartnerUpdateForm,
    Link,
    Coupon,
    Commission,
    Payout,
    PayoutItem,
    AuditLog
  } from '$lib/affiliate-admin/types';
  import type { ColDef, GridOptions } from 'ag-grid-community';

  const i18n = getContext('i18n');

  let partner: PartnerDetail | null = null;
  let links: Link[] = [];
  let coupons: Coupon[] = [];
  let commissions: Commission[] = [];
  let payouts: Payout[] = [];
  let payoutItems: PayoutItem[] = [];
  let loading = false;

  let showEdit = false;
  let editForm: PartnerUpdateForm = {
    name: '',
    email: '',
    status: 'active',
    payout_method: '',
    payout_details: {},
    rates: {},
    terms_version: ''
  };
  let payoutDetailsText = '';
  let ratesText = '';

  let showConfirm = false;
  let confirmMessage = '';
  let confirmAction: () => void | Promise<void> = async () => {};

  const gridOptions: GridOptions = { domLayout: 'autoHeight' };

  const linkCols: ColDef[] = [
    { headerName: 'Code', field: 'code' },
    { headerName: 'URL', field: 'url' },
    { headerName: 'Active', field: 'active' }
  ];

  const couponCols: ColDef[] = [
    { headerName: 'Code', field: 'code' },
    { headerName: 'Discount', field: 'discount_percent' },
    { headerName: 'Expires', field: 'expires_at' },
    { headerName: 'Active', field: 'active' }
  ];

  const commissionCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Order', field: 'order_id' },
    { headerName: 'Type', field: 'type' },
    { headerName: 'Status', field: 'status' },
    { headerName: 'Amount', field: 'amount' }
  ];

  const payoutCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Requested', field: 'requested_amount' },
    { headerName: 'Total', field: 'total_amount' },
    { headerName: 'Status', field: 'status' }
  ];

  const payoutItemCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Payout', field: 'payout_id' },
    { headerName: 'Commission', field: 'commission_id' },
    { headerName: 'Amount', field: 'amount' }
  ];

  const auditLogCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Actor', field: 'actor_id' },
    { headerName: 'Action', field: 'action' },
    { headerName: 'Resource', field: 'resource' },
    { headerName: 'Timestamp', field: 'timestamp' }
  ];

  onMount(async () => {
    loading = true;
    const token = localStorage.token;
    const partnerId = $page.params.partnerId;

    if (!partnerId) throw new Error('Missing partner ID');
    try {
      const [p, l, cpn, comm, pay] = await Promise.all([
        getPartner(token, partnerId),
        listLinks(token, { partner_id: partnerId }),
        listCoupons(token, { partner_id: partnerId }),
        listCommissions(token, { partner_id: partnerId }),
        listPayouts(token, { partner_id: partnerId })
      ]);

      partner = p;
      links = l;
      coupons = cpn;
      commissions = comm;
      payouts = pay;
      const details = await Promise.all(pay.map((p) => getPayout(token, p.id)));
      payoutItems = details.flatMap((d) => d.items);
    } finally {
      loading = false;
    }
  });

  function openEdit() {
    if (!partner) return;
    editForm = {
      name: partner.name,
      email: partner.email,
      status: partner.status,
      payout_method: partner.payout_method,
      payout_details: partner.payout_details,
      rates: partner.rates,
      terms_version: partner.terms_version
    };
    payoutDetailsText = JSON.stringify(partner.payout_details || {}, null, 2);
    ratesText = JSON.stringify(partner.rates || {}, null, 2);
    showEdit = true;
  }

  async function submitEdit() {
    if (!partner) return;
    try {
      editForm.payout_details = payoutDetailsText ? JSON.parse(payoutDetailsText) : {};
      editForm.rates = ratesText ? JSON.parse(ratesText) : {};
    } catch (e) {
      console.error('Invalid JSON', e);
      return;
    }
    const updated = await updatePartner(localStorage.token, partner.id, editForm);
    partner = updated;
    showEdit = false;
  }

  function confirmStatus() {
    if (!partner) return;
    if (partner.status === 'active') {
      confirmMessage = `${$i18n.t('Suspend')} ${partner.name}?`;
      confirmAction = async () => {
        await suspendPartner(localStorage.token, partner!.id);
        partner = { ...partner!, status: 'suspended' };
      };
    } else {
      confirmMessage = `${$i18n.t('Activate')} ${partner.name}?`;
      confirmAction = async () => {
        await activatePartner(localStorage.token, partner!.id);
        partner = { ...partner!, status: 'active' };
      };
    }
    showConfirm = true;
  }
</script>

<div class="space-y-6 text-gray-800 dark:text-gray-200">
  {#if partner}
    <div class="space-y-2">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-2xl font-semibold">{partner.name}</h1>
          <p>{partner.email}</p>
        </div>
        <div class="flex gap-2">
          <button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={openEdit}>
            {$i18n.t('Edit')}
          </button>
          {#if partner.status === 'active'}
            <button class="px-3 py-1 rounded bg-red-600 text-white" on:click={confirmStatus}>
              {$i18n.t('Suspend')}
            </button>
          {:else}
            <button class="px-3 py-1 rounded bg-green-600 text-white" on:click={confirmStatus}>
              {$i18n.t('Activate')}
            </button>
          {/if}
        </div>
      </div>
      <p>{$i18n.t('Role')}: {partner.role}</p>
      <p>{$i18n.t('Status')}: {partner.status}</p>
      <p>{$i18n.t('Balance')}: {partner.balance}</p>
      <p>{$i18n.t('Payout Method')}: {partner.payout_method}</p>
      <p>{$i18n.t('Terms Version')}: {partner.terms_version}</p>
      <div>
        <p class="font-semibold">{$i18n.t('Payout Details')}</p>
        <pre class="bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">{JSON.stringify(partner.payout_details, null, 2)}</pre>
      </div>
      <div>
        <p class="font-semibold">{$i18n.t('Rates')}</p>
        <pre class="bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">{JSON.stringify(partner.rates, null, 2)}</pre>
      </div>
    </div>
  {/if}

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Links')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if links.length === 0}
      <EmptyState title={$i18n.t('No links')} />
    {:else}
      <DataGrid columnDefs={linkCols} rowData={links} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Coupons')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if coupons.length === 0}
      <EmptyState title={$i18n.t('No coupons')} />
    {:else}
      <DataGrid columnDefs={couponCols} rowData={coupons} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Commissions')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if commissions.length === 0}
      <EmptyState title={$i18n.t('No commissions')} />
    {:else}
      <DataGrid columnDefs={commissionCols} rowData={commissions} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Payouts')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if payouts.length === 0}
      <EmptyState title={$i18n.t('No payouts')} />
    {:else}
      <DataGrid columnDefs={payoutCols} rowData={payouts} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Payout Items')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if payoutItems.length === 0}
      <EmptyState title={$i18n.t('No payout items')} />
    {:else}
      <DataGrid columnDefs={payoutItemCols} rowData={payoutItems} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Audit Logs')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if !partner || partner.audit_logs.length === 0}
      <EmptyState title={$i18n.t('No audit logs')} />
    {:else}
      <DataGrid columnDefs={auditLogCols} rowData={partner.audit_logs} {gridOptions} />
    {/if}
  </section>
</div>

<Modal bind:show={showEdit} onClose={() => (showEdit = false)}>
  <div class="p-4 space-y-4 text-gray-800 dark:text-gray-200">
    <h2 class="text-lg font-semibold">{$i18n.t('Edit Partner')}</h2>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Name')}</label>
      <input class="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={editForm.name} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Email')}</label>
      <input class="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={editForm.email} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Status')}</label>
      <select class="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={editForm.status}>
        <option value="active">{$i18n.t('Active')}</option>
        <option value="inactive">{$i18n.t('Inactive')}</option>
        <option value="suspended">{$i18n.t('Suspended')}</option>
      </select>
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Payout Method')}</label>
      <input class="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={editForm.payout_method} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Terms Version')}</label>
      <input class="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={editForm.terms_version} />
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Payout Details')}</label>
      <textarea class="w-full p-2 border rounded font-mono text-sm h-24 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={payoutDetailsText}></textarea>
    </div>
    <div class="space-y-2">
      <label class="block text-sm">{$i18n.t('Rates')}</label>
      <textarea class="w-full p-2 border rounded font-mono text-sm h-24 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-700" bind:value={ratesText}></textarea>
    </div>
    <div class="flex justify-end gap-2">
      <button class="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200" on:click={() => (showEdit = false)}>{$i18n.t('Cancel')}</button>
      <button class="px-3 py-1 rounded bg-blue-600 text-white" on:click={submitEdit}>{$i18n.t('Save')}</button>
    </div>
  </div>
</Modal>

<ConfirmDialog bind:show={showConfirm} title={$i18n.t('Confirm')} message={confirmMessage} onConfirm={confirmAction} />

