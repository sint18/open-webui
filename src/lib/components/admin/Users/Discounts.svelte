<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import {
		getDiscountCodes,
		deleteDiscountCode,
		getDiscountCodeUsers,
		type DiscountCode
	} from '$lib/apis/discounts';
	import { user } from '$lib/stores';
	import dayjs from '$lib/dayjs';
	import CreateDiscountModal from './Discounts/CreateDiscountModal.svelte';
	import EditDiscountModal from './Discounts/EditDiscountModal.svelte';
	import ViewUsageModal from './Discounts/ViewUsageModal.svelte';

	const i18n: any = getContext('i18n');

	// Data and state
	let discounts: DiscountCode[] = [];
	let loading = true;
	let statusFilter = 'all';
	let searchCode = '';
	let deletingCodeId: string | null = null;

	// Modal states
	let showCreateModal = false;
	let showEditModal = false;
	let showUsageModal = false;
	let selectedDiscount: DiscountCode | null = null;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		}
		await loadDiscounts();
	});

	async function loadDiscounts() {
		loading = true;
		try {
			discounts = await getDiscountCodes(localStorage.token);
		} catch (error) {
			console.error('Failed to load discount codes:', error);
			toast.error('Failed to load discount codes');
		} finally {
			loading = false;
		}
	}

	async function handleFilterChange() {
		// Apply client-side filtering since the API returns all codes
		// In a real implementation, you might want to add server-side filtering
	}

	async function handleDeleteDiscount(discountId: string, code: string) {
		if (
			!confirm(
				`Are you sure you want to delete the discount code "${code}"? This action cannot be undone.`
			)
		) {
			return;
		}

		try {
			deletingCodeId = discountId;
			await deleteDiscountCode(localStorage.token, discountId);
			toast.success('Discount code deleted successfully');
			await loadDiscounts();
		} catch (error) {
			console.error('Failed to delete discount code:', error);
			toast.error('Failed to delete discount code');
		} finally {
			deletingCodeId = null;
		}
	}

	function openCreateModal() {
		showCreateModal = true;
	}

	function openEditModal(discount: DiscountCode) {
		selectedDiscount = discount;
		showEditModal = true;
	}

	function openUsageModal(discount: DiscountCode) {
		selectedDiscount = discount;
		showUsageModal = true;
	}

	function closeModals() {
		showCreateModal = false;
		showEditModal = false;
		showUsageModal = false;
		selectedDiscount = null;
	}

	function getStatusBadgeClass(discount: DiscountCode) {
		if (!discount.active) {
			return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}

		// Check if expired
		if (discount.expires_at && new Date(discount.expires_at * 1000) < new Date()) {
			return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
		}

		// Check if usage limit reached
		if (discount.usage_limit && discount.used_count >= discount.usage_limit) {
			return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
		}

		return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
	}

	function getStatusText(discount: DiscountCode) {
		if (!discount.active) return 'Inactive';
		if (discount.expires_at && new Date(discount.expires_at * 1000) < new Date()) return 'Expired';
		if (discount.usage_limit && discount.used_count >= discount.usage_limit) return 'Limit Reached';
		return 'Active';
	}

	function formatDate(timestamp: number | null | undefined) {
		if (!timestamp) return '-';
		return dayjs(timestamp * 1000).format('MMM D, YYYY');
	}

	// Apply filters
	$: filteredDiscounts = discounts.filter((discount) => {
		// Status filter
		if (statusFilter === 'active' && !discount.active) return false;
		if (statusFilter === 'inactive' && discount.active) return false;
		if (
			statusFilter === 'expired' &&
			(!discount.expires_at || new Date(discount.expires_at * 1000) >= new Date())
		)
			return false;

		// Search filter
		if (searchCode && !discount.code.toLowerCase().includes(searchCode.toLowerCase())) return false;

		return true;
	});
</script>

<div class="w-full h-full flex flex-col space-y-4">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
		<div>
			<h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
				{$i18n.t('Discount Codes')}
			</h1>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('Manage promo codes and discount offers')}
			</p>
		</div>
		<button
			on:click={openCreateModal}
			class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
		>
			<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"
				></path>
			</svg>
			{$i18n.t('Create Discount Code')}
		</button>
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
				<option value="all">{$i18n.t('All Codes')}</option>
				<option value="active">{$i18n.t('Active')}</option>
				<option value="inactive">{$i18n.t('Inactive')}</option>
				<option value="expired">{$i18n.t('Expired')}</option>
			</select>
		</div>

		<div class="flex flex-col space-y-1 flex-1">
			<label for="code-search" class="text-sm font-medium text-gray-700 dark:text-gray-300">
				{$i18n.t('Search by code')}
			</label>
			<input
				id="code-search"
				type="text"
				bind:value={searchCode}
				on:input={handleFilterChange}
				placeholder={$i18n.t('Enter discount code...')}
				class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
			/>
		</div>
	</div>

	<!-- Discount Codes Table -->
	<div class="bg-white dark:bg-gray-900 rounded-lg shadow overflow-hidden">
		{#if loading && discounts.length === 0}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>
		{:else if filteredDiscounts.length === 0}
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
					{$i18n.t('No discount codes found')}
				</h3>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					{$i18n.t('Get started by creating a new discount code.')}
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
								{$i18n.t('Code')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
							>
								{$i18n.t('Discount')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
							>
								{$i18n.t('Usage')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
							>
								{$i18n.t('Expiry Date')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
							>
								{$i18n.t('Status')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
							>
								{$i18n.t('Actions')}
							</th>
						</tr>
					</thead>
					<tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
						{#each filteredDiscounts as discount}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm font-mono font-medium text-gray-900 dark:text-white">
										{discount.code}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
									{discount.discount_percent}%
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
									<div class="flex items-center space-x-2">
										<span>{discount.used_count}</span>
										{#if discount.usage_limit}
											<span class="text-gray-500">/ {discount.usage_limit}</span>
										{:else}
											<span class="text-gray-500">/ ∞</span>
										{/if}
										{#if discount.used_count > 0}
											<button
												on:click={() => openUsageModal(discount)}
												class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-xs"
											>
												{$i18n.t('View')}
											</button>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
									{formatDate(discount.expires_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span
										class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusBadgeClass(
											discount
										)}"
									>
										{getStatusText(discount)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm space-x-2">
									<button
										on:click={() => openEditModal(discount)}
										class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
									>
										{$i18n.t('Edit')}
									</button>
									<button
										on:click={() => {
											if (discount.id) {
												handleDeleteDiscount(discount.id, discount.code);
											}
										}}
										disabled={deletingCodeId === discount.id}
										class="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
									>
										{#if deletingCodeId === discount.id}
											<svg class="animate-spin h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24">
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
											{$i18n.t('Deleting...')}
										{:else}
											{$i18n.t('Delete')}
										{/if}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<!-- Modals -->
{#if showCreateModal}
	<CreateDiscountModal
		on:close={closeModals}
		on:created={() => {
			closeModals();
			loadDiscounts();
		}}
	/>
{/if}

{#if showEditModal && selectedDiscount}
	<EditDiscountModal
		discount={selectedDiscount}
		on:close={closeModals}
		on:updated={() => {
			closeModals();
			loadDiscounts();
		}}
	/>
{/if}

{#if showUsageModal && selectedDiscount}
	<ViewUsageModal discount={selectedDiscount} on:close={closeModals} />
{/if}
