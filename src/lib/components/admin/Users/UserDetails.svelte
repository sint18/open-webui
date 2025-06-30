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
		try {
			const [creditsData, transactionsData, ordersData, userInfo] = await Promise.all([
				getUserCreditsByUserId(localStorage.token, userId),
				getTransactionsByUserId(localStorage.token, userId),
				getPaymentOrdersByUserId(localStorage.token, userId),
				getUserById(localStorage.token, userId)
			]);
			credits = creditsData;
			transactions = transactionsData;
			orders = ordersData;
			userDetails = userInfo;
		} catch (error) {
			toast.error('Failed to load user billing data');
			console.error(error);
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
				<p class="text-gray-500">No credit information available</p>
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
