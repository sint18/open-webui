<script lang="ts">
        import { onMount, getContext } from 'svelte';
        import { goto } from '$app/navigation';
        import { page } from '$app/stores';
        import { user } from '$lib/stores';

        const i18n = getContext('i18n');

        let loaded = false;

        const routeLabels: Record<string, string> = {
                applications: 'Applications',
                partners: 'Partners',
                links: 'Links',
                coupons: 'Coupons',
                commissions: 'Commissions',
                payouts: 'Payouts',
                fraud: 'Fraud',
                reports: 'Reports',
                settings: 'Settings',
                audit: 'Audit',
                'order-lookup': 'Order Lookup'
        };

        let segment = '';
        $: segment = $page.url.pathname.split('/')[3] || '';
        $: currentLabel = routeLabels[segment];

        const allowedRoles = ['admin', 'finance', 'support', 'partner-manager'];

        onMount(async () => {
                if (!$user || !allowedRoles.includes($user.role)) {
                        await goto('/403');
                        return;
                }
                loaded = true;
        });
</script>

<svelte:head>
        <title>{`${$i18n.t('Affiliate')} • ${$i18n.t('Admin Panel')}`}</title>
</svelte:head>

{#if loaded}
        <div class="p-4 text-gray-800 dark:text-gray-200">
                <nav class="text-sm mb-4 text-gray-500 dark:text-gray-400">
                        <a href="/admin" class="hover:underline">{$i18n.t('Admin')}</a>
                        <span class="mx-1">/</span>
                        <a href="/admin/affiliate" class="hover:underline">{$i18n.t('Affiliate')}</a>
                        {#if currentLabel}
                                <span class="mx-1">/</span>
                                <span>{$i18n.t(currentLabel)}</span>
                        {/if}
                </nav>
                <slot />
        </div>
{/if}
