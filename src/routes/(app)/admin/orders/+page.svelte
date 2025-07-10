<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { getAllPaymentOrders, confirmPaymentOrder } from '$lib/apis/billing';
	import { user } from '$lib/stores';
	import dayjs from '$lib/dayjs';

	const i18n = getContext('i18n');

	// Data and state
	let orders = [];
	let loading = true;
	let statusFilter = 'all';
	let searchEmail = '';
	let confirmingOrderId = null;

	// Pagination
	let skip = 0;
	let limit = 50;
	let hasMore = true;

	onMount(async () => {
		// Only admin users should access this page
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}

		await loadOrders(true);
	});

	async function loadOrders(reset = false) {
		try {
			loading = true;
			if (reset) {
				skip = 0;
				orders = [];
				hasMore = true;
			}

			const filters = {
				skip,
				limit,
				status: statusFilter === 'all' ? undefined : statusFilter,
				userEmail: searchEmail.trim() || undefined
			};

			const newOrders = await getAllPaymentOrders(
				localStorage.token,
				filters.skip,
				filters.limit,
				filters.status,
				filters.userEmail
			);

			if (reset) {
				orders = newOrders;
			} else {
				orders = [...orders, ...newOrders];
			}

			hasMore = newOrders.length === limit;
			skip += limit;
		} catch (error) {
			console.error('Failed to load orders:', error);
			toast.error('Failed to load orders');
		} finally {
			loading = false;
		}
	}

	async function handleFilterChange() {
		await loadOrders(true);
	}

	async function handleConfirmOrder(orderId: string) {
		try {
			confirmingOrderId = orderId;
			await confirmPaymentOrder(localStorage.token, orderId);
			toast.success('Payment confirmed successfully');
			await loadOrders(true); // Refresh the list
		} catch (error) {
			console.error('Failed to confirm order:', error);
			toast.error('Failed to confirm payment');
		} finally {
			confirmingOrderId = null;
		}
	}

	function viewUserDetails(userId: string) {
		goto(`/admin/users/${userId}`);
	}

	function getStatusBadgeClass(status: string) {
		switch (status) {
			case 'paid':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
			case 'pending':
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
			case 'failed':
				return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}
	}

	function formatAmount(amount: number) {
		return new Intl.NumberFormat('en-US').format(amount);
	}

	function viewScreenshot(screenshotPath: string) {
		if (screenshotPath) {
			// Open screenshot in new tab/window
			window.open(screenshotPath, '_blank');
		}
	}
</script>

<div class="flex flex-col w-full h-full">
	<div class="flex flex-col space-y-4">
		<!-- Header -->
		<div class="flex justify-between items-center">
			<h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
				{$i18n.t('Payment Orders Dashboard')}
			</h1>
		</div>

		<!-- Filters -->
		<div class="flex flex-col sm:flex-row gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
			<div class="flex flex-col space-y-1">
				<label class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$i18n.t('Status')}
				</label>
				<select
					bind:value={statusFilter}
					on:change={handleFilterChange}
					class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">{$i18n.t('All Orders')}</option>
					<option value="pending">{$i18n.t('Pending')}</option>
					<option value="paid">{$i18n.t('Paid')}</option>
					<option value="failed">{$i18n.t('Failed')}</option>
				</select>
			</div>

			<div class="flex flex-col space-y-1 flex-1">
				<label class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$i18n.t('Search by user email')}
				</label>
				<input
					type="text"
					bind:value={searchEmail}
					on:input={handleFilterChange}
					placeholder={$i18n.t('Enter user email...')}
					class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
				/>
			</div>
		</div>

		<!-- Orders Table -->
		<div class="bg-white dark:bg-gray-900 rounded-lg shadow overflow-hidden">
			{#if loading && orders.length === 0}
				<div class="flex justify-center items-center py-12">
					<div
						class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"
					></div>
				</div>
			{:else if orders.length === 0}
				<div class="text-center py-12">
					<p class="text-gray-500 dark:text-gray-400">
						{$i18n.t('No orders found')}
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
									{$i18n.t('Order ID')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('User')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Amount')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Credits')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Status')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Date')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Screenshot')}
								</th>
								<th
									class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
								>
									{$i18n.t('Actions')}
								</th>
							</tr>
						</thead>
						<tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
							{#each orders as order}
								<tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
									<td
										class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white"
									>
										{order.order_id.substring(0, 8)}...
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="text-sm text-gray-900 dark:text-white">
											{order.user_name || 'Unknown'}
										</div>
										<div class="text-sm text-gray-500 dark:text-gray-400">
											{order.user_email || order.user_id}
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
										{formatAmount(order.amount_mmk)} MMK
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
										{order.credits || '-'}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span
											class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusBadgeClass(
												order.status
											)}"
										>
											{order.status}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
										{dayjs(order.created_at * 1000).format('MMM D, YYYY HH:mm')}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm">
										{#if order.screenshot_path}
											<button
												on:click={() => viewScreenshot(order.screenshot_path)}
												class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
											>
												{$i18n.t('View')}
											</button>
										{:else}
											<span class="text-gray-400">-</span>
										{/if}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm space-x-2">
										{#if order.status === 'pending'}
											<button
												on:click={() => handleConfirmOrder(order.order_id)}
												disabled={confirmingOrderId === order.order_id}
												class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
											>
												{#if confirmingOrderId === order.order_id}
													<svg
														class="animate-spin -ml-1 mr-2 h-3 w-3 text-white"
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
													>
														<circle
															class="opacity-25"
															cx="12"
															cy="12"
															r="10"
															stroke="currentColor"
															stroke-width="4"
														></circle>
														<path
															class="opacity-75"
															fill="currentColor"
															d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
														></path>
													</svg>
													{$i18n.t('Confirming...')}
												{:else}
													{$i18n.t('Confirm')}
												{/if}
											</button>
										{/if}
										<button
											on:click={() => viewUserDetails(order.user_id)}
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

				<!-- Load More Button -->
				{#if hasMore}
					<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
						<button
							on:click={() => loadOrders(false)}
							disabled={loading}
							class="w-full py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
						>
							{#if loading}
								<svg
									class="animate-spin h-4 w-4 mx-auto"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
								>
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
									></path>
								</svg>
							{:else}
								{$i18n.t('Load More')}
							{/if}
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
