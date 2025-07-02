<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<i18nType>('i18n');

	let mounted = false;

	interface LowCreditEvent extends CustomEvent {
		detail: {
			remaining: number;
			used: number;
			limit: number;
			percent: number;
		};
	}

	const handleLowCreditWarning = (event: LowCreditEvent) => {
		if (!mounted) return;

		const { remaining, used, limit, percent } = event.detail;

		// Use toast.warning with inline HTML-like structure
		toast.warning(
			`🚨 Credits Running Low\n\nYou have ${remaining.toFixed(1)}% credits remaining \nUpgrade your plan to continue using the service.`,
			{
				duration: 10000,
				position: 'top-center',
				dismissable: true,
				action: {
					label: i18n?.t ? i18n.t('Upgrade Plan') : 'Upgrade Plan',
					onClick: () => goto('/pricing')
				},
				// cancel: {
				// 	label: i18n?.t ? i18n.t('Dismiss') : 'Dismiss',
				// 	onClick: () => {}
				// },
				style:
					'background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; color: #92400e; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.3);'
			}
		);
	};

	onMount(() => {
		mounted = true;
		window.addEventListener('low-credit-warning', handleLowCreditWarning as EventListener);
	});

	onDestroy(() => {
		mounted = false;
		window.removeEventListener('low-credit-warning', handleLowCreditWarning as EventListener);
	});
</script>
