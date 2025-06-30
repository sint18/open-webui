<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import {
		getTransactionsByUserId,
		getUserCreditsByUserId,
		getPaymentOrdersByUserId
	} from '$lib/apis/billing';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import { getUserById } from '$lib/apis/users';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import ConfirmPaymentModal from '$lib/components/admin/Users/ConfirmPaymentModal.svelte';

	export let userId: string;

	let loading = true;
	let credits = null;
	let transactions = [];
	let orders = [];
	let userDetails = null;
	let showConfirm = false;
	let selectedOrder = null;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		}
		await loadData();
	});

	async function loadData() {
		loading = true;
		try {
			// Use Promise.allSettled for graceful failure handling
			const [creditsResult, transactionsResult, ordersResult, userInfoResult] =
				await Promise.allSettled([
					getUserCreditsByUserId(localStorage.token, userId),
					getTransactionsByUserId(localStorage.token, userId),
					getPaymentOrdersByUserId(localStorage.token, userId),
					getUserById(localStorage.token, userId)
				]);

			// Handle credits (may not exist for new users)
			if (creditsResult.status === 'fulfilled') {
				credits = creditsResult.value;
			} else {
				console.warn('No credit record found for user:', userId);
				credits = null;
			}

			// Handle transactions (may be empty for new users)
			if (transactionsResult.status === 'fulfilled') {
				transactions = transactionsResult.value || [];
			} else {
				console.warn('No transactions found for user:', userId);
				transactions = [];
			}

			// Handle orders (should always exist if user made purchases)
			if (ordersResult.status === 'fulfilled') {
				orders = ordersResult.value || [];
			} else {
				console.error('Failed to fetch orders for user:', userId);
				orders = [];
			}

			// Handle user info (should always exist)
			if (userInfoResult.status === 'fulfilled') {
				userDetails = userInfoResult.value;
			} else {
				console.error('Failed to fetch user details:', userId);
				throw new Error('User not found');
			}
		} catch (error) {
			console.error('Critical error loading user data:', error);
			toast.error('Failed to load user data');
		} finally {
			loading = false;
		}
	}

	function openConfirm(order) {
		console.log(order);
		selectedOrder = order;
		showConfirm = true;
	}

	function closeModal() {
		showConfirm = false;
		selectedOrder = null;
	}
</script>

{#if loading}
	<div class="my-10">
		<Spinner />
	</div>
{:else}
	<div class="space-y-6">
		<div class="bg-white dark:bg-gray-900 rounded-lg p-6">
			<h2 class="text-lg font-semibold mb-4">User Information</h2>
			{#if userDetails}
				<div class="grid grid-cols-2 gap-4">
					<div>
						<p class="text-sm text-gray-500">Name</p>
						<p class="text-lg font-medium">{userDetails.name || 'N/A'}</p>
					</div>
					<div>
						<p class="text-sm text-gray-500">Active Now</p>
						<p class="text-lg font-medium">
							{userDetails.active}
						</p>
					</div>
				</div>
			{:else}
				<p class="text-gray-500">No user information available</p>
			{/if}
		</div>

		<!-- Credits Information -->
		<div class="bg-white dark:bg-gray-900 rounded-lg p-6">
			<h2 class="text-lg font-semibold mb-4">Credits & Subscription</h2>
			{#if credits}
				<div class="grid grid-cols-2 gap-4">
					<div>
						<p class="text-sm text-gray-500">Current Plan</p>
						<p class="text-lg font-medium">{credits.plan_id}</p>
					</div>
					<div>
						<p class="text-sm text-gray-500">Credit Balance</p>
						<p class="text-lg font-medium">{credits.credit_balance}</p>
					</div>
					<div>
						<p class="text-sm text-gray-500">Monthly Quota</p>
						<p class="text-lg font-medium">{credits.monthly_quota}</p>
					</div>
					<div>
						<p class="text-sm text-gray-500">Status</p>
						<Badge
							type={credits.status === 'active'
								? 'success'
								: credits.status === 'grace'
									? 'warning'
									: 'error'}
							content={credits.status}
						/>
					</div>
					{#if credits.current_period_end}
						<div class="col-span-2">
							<p class="text-sm text-gray-500">Subscription Ends</p>
							<p class="text-lg font-medium">
								{dayjs(credits.current_period_end * 1000).format('LL')}
							</p>
						</div>
					{/if}
				</div>
			{:else}
				<div
					class="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
				>
					<div class="flex">
						<div class="flex-shrink-0">
							<svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
								<path
									fill-rule="evenodd"
									d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
						<div class="ml-3">
							<h3 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
								No Credit Record
							</h3>
							<div class="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
								<p>
									This user hasn't been assigned credits yet. Credits will be created when their
									first payment is confirmed.
								</p>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Transactions -->
		<div class="bg-white dark:bg-gray-900 rounded-lg p-6">
			<h2 class="text-lg font-semibold mb-4">Recent Transactions</h2>
			{#if transactions.length > 0}
				<div class="overflow-x-auto">
					<table class="min-w-full">
						<thead>
							<tr class="text-left text-sm text-gray-500">
								<th class="pb-2">Date</th>
								<th class="pb-2">Model</th>
								<th class="pb-2">Credits</th>
								<th class="pb-2">USD</th>
							</tr>
						</thead>
						<tbody>
							{#each transactions as tx}
								<tr class="border-t dark:border-gray-800">
									<td class="py-2">
										{dayjs(tx.created_at * 1000).format('MMM D, YYYY')}
									</td>
									<td class="py-2">{tx.model_name}</td>
									<td class="py-2">
										<span class={tx.delta < 0 ? 'text-red-500' : 'text-green-500'}>
											{tx.delta > 0 ? '+' : ''}{tx.delta}
										</span>
									</td>
									<td class="py-2">${tx.usd_spend}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="text-gray-500">No transactions found</p>
			{/if}
		</div>

		<!-- Payment Orders section -->
		<div class="bg-white dark:bg-gray-900 rounded-lg p-6">
			<h2 class="text-lg font-semibold mb-4">Payment Orders</h2>
			{#if orders.length > 0}
				<div class="overflow-x-auto">
					<table class="min-w-full">
						<thead>
							<tr class="text-left text-sm text-gray-500">
								<th class="pb-2">Date</th>
								<th class="pb-2">Type</th>
								<th class="pb-2">Amount</th>
								<th class="pb-2">Status</th>
								<th class="pb-2">Screenshot</th>
								<th class="pb-2"></th>
							</tr>
						</thead>
						<tbody>
							{#each orders as order}
								<tr class="border-t dark:border-gray-800">
									<td class="py-2">
										{dayjs(order.created_at * 1000).format('LL')}
									</td>
									<td class="py-2">{order.type}</td>
									<td class="py-2">{order.amount_mmk} MMK</td>
									<td class="py-2">
										<Badge
											type={order.status === 'paid'
												? 'success'
												: order.status === 'pending'
													? 'warning'
													: 'error'}
											content={order.status}
										/>
									</td>
									<td class="py-2">
										{#if order.screenshot_path}
											<button
												class="text-blue-500 hover:text-blue-700"
												on:click={() => {
													// Open image in a modal or new window
													window.open(
														`${WEBUI_API_BASE_URL}/api/storage/${order.screenshot_path}`,
														'_blank'
													);
												}}
											>
												View Screenshot
											</button>
										{:else}
											<span class="text-gray-400">No screenshot</span>
										{/if}
									</td>
									<td class="py-2">
										{#if order.status === 'pending'}
											<button class="btn btn-sm btn-primary" on:click={() => openConfirm(order)}>
												Confirm Payment
											</button>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="text-gray-500">No payment orders found</p>
			{/if}
		</div>
	</div>
{/if}

{#if showConfirm && selectedOrder}
	<ConfirmPaymentModal
		orderId={selectedOrder.order_id}
		on:close={closeModal}
		on:confirmed={loadData}
	/>
{/if}
