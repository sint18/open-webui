<script lang="ts">
  import { getContext, onMount } from 'svelte';
  import { page } from '$app/stores';
  import {
    DataGrid,
    DataGridSkeleton,
    EmptyState
  } from '$lib/affiliate-admin/components';
  import {
    getPartner,
    listLinks,
    listCoupons,
    listClicks,
    listAttributions,
    listCommissions,
    listPayouts,
    getPayout
  } from '$lib/affiliate-admin/api';
  import type {
    PartnerDetail,
    Link,
    Coupon,
    Click,
    Attribution,
    Commission,
    Payout,
    PayoutItem
  } from '$lib/affiliate-admin/types';
  import type { ColDef, GridOptions } from 'ag-grid-community';

  const i18n = getContext('i18n');

  let partner: PartnerDetail | null = null;
  let links: Link[] = [];
  let coupons: Coupon[] = [];
  let clicks: Click[] = [];
  let attributions: Attribution[] = [];
  let commissions: Commission[] = [];
  let payouts: Payout[] = [];
  let payoutItems: PayoutItem[] = [];
  let loading = false;

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

  const clickCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Link', field: 'link_id' },
    { headerName: 'Coupon', field: 'coupon_id' },
    { headerName: 'Created', field: 'created_at' }
  ];

  const attributionCols: ColDef[] = [
    { headerName: 'ID', field: 'id' },
    { headerName: 'Click', field: 'click_id' },
    { headerName: 'Via', field: 'attr_via' },
    { headerName: 'Created', field: 'created_at' }
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
</script>

<div class="space-y-6 text-gray-800 dark:text-gray-200">
  {#if partner}
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold">{partner.name}</h1>
      <p>{partner.email}</p>
      <p>{$i18n.t('Status')}: {partner.status}</p>
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
    <h2 class="text-lg font-semibold">{$i18n.t('Clicks')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if clicks.length === 0}
      <EmptyState title={$i18n.t('No clicks')} />
    {:else}
      <DataGrid columnDefs={clickCols} rowData={clicks} {gridOptions} />
    {/if}
  </section>

  <section>
    <h2 class="text-lg font-semibold">{$i18n.t('Attributions')}</h2>
    {#if loading}
      <DataGridSkeleton />
    {:else if attributions.length === 0}
      <EmptyState title={$i18n.t('No attributions')} />
    {:else}
      <DataGrid columnDefs={attributionCols} rowData={attributions} {gridOptions} />
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
</div>

