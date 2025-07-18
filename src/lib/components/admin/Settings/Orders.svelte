<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { getAllPaymentOrders, confirmPaymentOrder, declinePaymentOrder } from '$lib/apis/billing';
	import { user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import dayjs from '$lib/dayjs';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import { trackEvent, ANALYTICS_EVENTS } from '$lib/utils/analytics';

	const i18n: any = getContext('i18n');

	// Type definitions
	interface PaymentOrder {
		order_id: string;
		user_id: string;
		user_name?: string;
		user_email?: string;
		amount_mmk: number;
		credits?: number;
		status: string;
		created_at: number;
		screenshot_path?: string;
		plan_id?: string;
		provider?: string;
	}

	// Data and state
	let orders: PaymentOrder[] = [];
	let loading = true;
	let statusFilter = 'all';
	let searchEmail = '';
	let confirmingOrderId: string | null = null;
	let decliningOrderId: string | null = null;

	// Confirmation dialog state
	let showConfirmDialog = false;
	let selectedOrderForConfirmation: PaymentOrder | null = null;

	// Decline dialog state
	let showDeclineDialog = false;
	let selectedOrderForDecline: PaymentOrder | null = null;

	// Pagination
	let skip = 0;
	let limit = 50;
	let hasMore = true;

	onMount(async () => {
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

	function showConfirmationDialog(order: PaymentOrder) {
		selectedOrderForConfirmation = order;
		showConfirmDialog = true;
	}

	function showDeclineConfirmationDialog(order: PaymentOrder) {
		selectedOrderForDecline = order;
		showDeclineDialog = true;
	}

	async function handleConfirmOrder(orderId: string) {
		try {
			confirmingOrderId = orderId;

			// Find the order details for tracking
			const order = orders.find((o) => o.order_id === orderId);

			await confirmPaymentOrder(localStorage.token, orderId);

			// Track subscription completion
			if (order) {
				trackEvent(ANALYTICS_EVENTS.SUBSCRIPTION_COMPLETED, {
					order_id: orderId,
					user_id: order.user_id,
					user_email: order.user_email,
					plan_id: order.plan_id || 'unknown',
					amount_mmk: order.amount_mmk,
					credits: order.credits,
					provider: order.provider || 'unknown',
					admin_confirmed: true,
					admin_user_id: $user?.id,
					admin_email: $user?.email
				});
			}

			toast.success('Payment confirmed successfully');
			await loadOrders(true); // Refresh the list
		} catch (error) {
			console.error('Failed to confirm order:', error);
			toast.error('Failed to confirm payment');
		} finally {
			confirmingOrderId = null;
		}
	}

	async function handleDeclineOrder(orderId: string) {
		try {
			decliningOrderId = orderId;
			console.log('Declining order:', orderId);
			await declinePaymentOrder(localStorage.token, orderId);
			toast.success('Payment declined successfully');
			await loadOrders(true); // Refresh the list
		} catch (error) {
			console.error('Failed to decline order:', error);
			const errorMessage = error instanceof Error ? error.message : 'Failed to decline payment';
			toast.error(`Decline failed: ${errorMessage}`);
		} finally {
			decliningOrderId = null;
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
			case 'declined':
				return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}
	}

	function formatAmount(amount: number) {
		return new Intl.NumberFormat('en-US').format(amount);
	}

	async function viewScreenshot(screenshotPath: string | undefined) {
		if (screenshotPath) {
			try {
				// Fetch the file through the authenticated API
				const response = await fetch(`${WEBUI_API_BASE_URL}/storage/${screenshotPath}`, {
					headers: {
						Authorization: `Bearer ${localStorage.token}`
					}
				});

				if (!response.ok) {
					throw new Error('Failed to fetch screenshot');
				}

				// Create a blob URL and open in new window
				const blob = await response.blob();
				const blobUrl = URL.createObjectURL(blob);
				const newWindow = window.open(blobUrl, '_blank');

				// Clean up the blob URL after some time to prevent memory leaks
				if (newWindow) {
					newWindow.addEventListener('beforeunload', () => {
						URL.revokeObjectURL(blobUrl);
					});
					// Also cleanup after 5 minutes as a fallback
					setTimeout(() => URL.revokeObjectURL(blobUrl), 300000);
				} else {
					// If popup was blocked, cleanup immediately
					URL.revokeObjectURL(blobUrl);
				}
			} catch (error) {
				console.error('Error viewing screenshot:', error);
				toast.error('Failed to load screenshot');
			}
		}
	}
</script>

<div class="flex flex-col w-full space-y-4">
	<!-- Header -->
	<div class="flex justify-between items-center">
		<div>
			<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
				{$i18n.t('Payment Orders')}
			</h2>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				{$i18n.t('Manage and review all payment orders across all users')}
			</p>
		</div>
	</div>

	<!-- Filters -->
	<div class="flex flex-col sm:flex-row gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
		<div class="flex flex-col space-y-1">
			<label for="status-filter" class="text-sm font-medium text-gray-700 dark:text-gray-300">
				{$i18n.t('Status')}
			</label>
			<select
				id="status-filter"
				bind:value={statusFilter}
				on:change={handleFilterChange}
				class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
			>
				<option value="all">{$i18n.t('All Orders')}</option>
				<option value="pending">{$i18n.t('Pending')}</option>
				<option value="paid">{$i18n.t('Paid')}</option>
				<option value="failed">{$i18n.t('Failed')}</option>
				<option value="declined">{$i18n.t('Declined')}</option>
			</select>
		</div>

		<div class="flex flex-col space-y-1 flex-1">
			<label for="email-search" class="text-sm font-medium text-gray-700 dark:text-gray-300">
				{$i18n.t('Search by user email')}
			</label>
			<input
				id="email-search"
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
											on:click={() => showConfirmationDialog(order)}
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
										<button
											on:click={() => showDeclineConfirmationDialog(order)}
											disabled={decliningOrderId === order.order_id}
											class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
										>
											{#if decliningOrderId === order.order_id}
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
												{$i18n.t('Declining...')}
											{:else}
												{$i18n.t('Decline')}
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

<!-- Confirmation Dialog -->
<ConfirmDialog
	bind:show={showConfirmDialog}
	title={$i18n.t('Confirm Payment')}
	message={selectedOrderForConfirmation
		? `Are you sure you want to confirm payment for order **${selectedOrderForConfirmation.order_id.substring(0, 8)}...** from user **${selectedOrderForConfirmation.user_email || selectedOrderForConfirmation.user_name || 'Unknown'}** for **${formatAmount(selectedOrderForConfirmation.amount_mmk)} MMK**? This action cannot be undone.`
		: $i18n.t('Are you sure you want to confirm this payment?')}
	confirmLabel={$i18n.t('Confirm Payment')}
	on:confirm={() => {
		if (selectedOrderForConfirmation) {
			handleConfirmOrder(selectedOrderForConfirmation.order_id);
		}
		selectedOrderForConfirmation = null;
	}}
	on:cancel={() => {
		selectedOrderForConfirmation = null;
	}}
/>

<!-- Decline Dialog -->
<ConfirmDialog
	bind:show={showDeclineDialog}
	title={$i18n.t('Decline Payment')}
	message={selectedOrderForDecline
		? `Are you sure you want to decline payment for order **${selectedOrderForDecline.order_id.substring(0, 8)}...** from user **${selectedOrderForDecline.user_email || selectedOrderForDecline.user_name || 'Unknown'}** for **${formatAmount(selectedOrderForDecline.amount_mmk)} MMK**? This action cannot be undone.`
		: $i18n.t('Are you sure you want to decline this payment?')}
	confirmLabel={$i18n.t('Decline Payment')}
	on:confirm={() => {
		if (selectedOrderForDecline) {
			handleDeclineOrder(selectedOrderForDecline.order_id);
		}
		selectedOrderForDecline = null;
	}}
	on:cancel={() => {
		selectedOrderForDecline = null;
	}}
/>
