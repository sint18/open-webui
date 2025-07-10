<script lang="ts">
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getDiscountCodeUsers, type DiscountCode, type DiscountUsage } from '$lib/apis/discounts';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/common/Modal.svelte';
	import dayjs from '$lib/dayjs';

	export let discount: DiscountCode;

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	let loading = true;
	let usageHistory: DiscountUsage[] = [];

	onMount(async () => {
		await loadUsageHistory();
	});

	async function loadUsageHistory() {
		loading = true;
		try {
			usageHistory = await getDiscountCodeUsers(localStorage.token, discount.code);
		} catch (error) {
			console.error('Failed to load usage history:', error);
			toast.error('Failed to load usage history');
		} finally {
			loading = false;
		}
	}

	function closeModal() {
		dispatch('close');
	}

	function viewUserDetails(userId: string) {
		goto(`/admin/users/${userId}`);
		closeModal();
	}

	function formatDate(timestamp: number) {
		return dayjs(timestamp * 1000).format('MMM D, YYYY HH:mm');
	}

	// Reactive variables for computed values
	$: uniqueUsersCount = new Set(usageHistory.map((u) => u.user_id)).size;
</script>

<Modal size="lg" on:close={closeModal}>
	<div class="bg-white dark:bg-gray-900 rounded-lg p-6">
		<div
			class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-4 mb-6"
		>
			<div class="flex items-center space-x-2">
				<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					></path>
				</svg>
				<span class="text-lg font-semibold text-gray-900 dark:text-white"
					>{$i18n.t('Usage History: {{code}}', { code: discount.code })}</span
				>
			</div>
			<button
				type="button"
				on:click={closeModal}
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					></path>
				</svg>
			</button>
		</div>
		<div class="space-y-4">
			<!-- Discount Info -->
			<div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Discount')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">{discount.discount_percent}%</p>
					</div>
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Times Used')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">{discount.used_count}</p>
					</div>
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Usage Limit')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">
							{discount.usage_limit || $i18n.t('Unlimited')}
						</p>
					</div>
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Expiry Date')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">
							{discount.expires_at
								? dayjs(discount.expires_at * 1000).format('MMM D, YYYY')
								: $i18n.t('No expiry')}
						</p>
					</div>
				</div>
			</div>

			<!-- Usage History Table -->
			<div
				class="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
			>
				{#if loading}
					<div class="flex justify-center items-center py-12">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					</div>
				{:else if usageHistory.length === 0}
					<div class="text-center py-12">
						<svg
							class="mx-auto h-12 w-12 text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 48 48"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.713-3.714M14 40v-4c0-1.313.253-2.566.713-3.714m0 0A9.971 9.971 0 0124 24c4.265 0 7.615 2.667 9.287 6.286"
							/>
						</svg>
						<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
							{$i18n.t('No usage history')}
						</h3>
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
							{$i18n.t('This discount code has not been used yet.')}
						</p>
					</div>
				{:else}
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
							<thead class="bg-gray-50 dark:bg-gray-800">
								<tr>
									<th
										class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
									>
										{$i18n.t('User')}
									</th>
									<th
										class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
									>
										{$i18n.t('Email')}
									</th>
									<th
										class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
									>
										{$i18n.t('Used At')}
									</th>
									<th
										class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
									>
										{$i18n.t('Actions')}
									</th>
								</tr>
							</thead>
							<tbody
								class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700"
							>
								{#each usageHistory as usage}
									<tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
										<td class="px-6 py-4 whitespace-nowrap">
											<div class="text-sm font-medium text-gray-900 dark:text-white">
												{usage.user_name || 'Unknown User'}
											</div>
											<div class="text-sm text-gray-500 dark:text-gray-400 font-mono">
												{usage.user_id}
											</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
											{usage.user_email || '-'}
										</td>
										<td
											class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
										>
											{formatDate(usage.used_at)}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm">
											<button
												on:click={() => viewUserDetails(usage.user_id)}
												class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
											>
												{$i18n.t('View User')}
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>

			<!-- Summary Stats -->
			{#if usageHistory.length > 0}
				<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
					<div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
						<p class="text-sm text-blue-600 dark:text-blue-400">{$i18n.t('Total Uses')}</p>
						<p class="text-2xl font-bold text-blue-900 dark:text-blue-100">{usageHistory.length}</p>
					</div>
					<div class="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
						<p class="text-sm text-green-600 dark:text-green-400">{$i18n.t('Unique Users')}</p>
						<p class="text-2xl font-bold text-green-900 dark:text-green-100">
							{uniqueUsersCount}
						</p>
					</div>
					<div class="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
						<p class="text-sm text-purple-600 dark:text-purple-400">{$i18n.t('Remaining Uses')}</p>
						<p class="text-2xl font-bold text-purple-900 dark:text-purple-100">
							{discount.usage_limit ? Math.max(0, discount.usage_limit - discount.used_count) : '∞'}
						</p>
					</div>
				</div>
			{/if}

			<!-- Close Button -->
			<div class="flex justify-end pt-4">
				<button
					type="button"
					on:click={closeModal}
					class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					{$i18n.t('Close')}
				</button>
			</div>
		</div>
	</div>
</Modal>
