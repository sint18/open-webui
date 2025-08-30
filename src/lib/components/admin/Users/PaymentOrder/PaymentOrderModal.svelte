<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { getAllUsers } from '$lib/apis/users';
	import { createManualPaymentOrder, updatePaymentOrder } from '$lib/apis/billing';
	import { toast } from 'svelte-sonner';

	export let show = false;
	export let order = null;

	let users = [];
	let selectedUserId = '';
	let orderType = 'manual';
        let planId = 'free';
        let credits = 0;
        let imageCredits = 0;
        let videoCredits = 0;
        let amount = 0;
        let provider = 'manual';
        let notes = '';

	const dispatch = createEventDispatcher();

	const initializeForm = (order) => {
		if (order) {
                        selectedUserId = order.user_id;
                        orderType = order.type;
                        planId = order.plan_id;
                        credits = order.credits;
                        imageCredits = order.image_credits;
                        videoCredits = order.video_credits;
                        amount = order.amount_mmk;
                        provider = order.provider;
                        notes = order.notes;
                } else {
                        selectedUserId = '';
                        orderType = 'manual';
                        planId = 'free';
                        credits = 0;
                        imageCredits = 0;
                        videoCredits = 0;
                        amount = 0;
                        provider = 'manual';
                        notes = '';
                }
        };

	$: initializeForm(order);

	onMount(async () => {
		const res = await getAllUsers(localStorage.token);
		users = res.users;
	});

	const close = () => {
		dispatch('close');
	};

	const handleSubmit = async () => {
		try {
			if (order) {
                                await updatePaymentOrder(localStorage.token, order.order_id, {
                                        user_id: selectedUserId,
                                        type: orderType,
                                        plan_id: planId,
                                        credits: credits,
                                        image_credits: imageCredits,
                                        video_credits: videoCredits,
                                        amount_mmk: amount,
                                        provider: provider,
                                        notes: notes
                                });
                                toast.success('Payment order updated successfully');
                        } else {
                                await createManualPaymentOrder(localStorage.token, {
                                        user_id: selectedUserId,
                                        type: orderType,
                                        plan_id: planId,
                                        credits: credits,
                                        image_credits: imageCredits,
                                        video_credits: videoCredits,
                                        amount_mmk: amount,
                                        provider: provider,
                                        notes: notes
                                });
                                toast.success('Payment order created successfully');
			}
			dispatch('save');
			close();
		} catch (error) {
			toast.error(error.message);
		}
	};
</script>

<Modal {show} on:close={close}>
	<div class="p-4">
		<!-- Header -->
		<div class="flex justify-between items-center border-b dark:border-gray-700">
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
				{#if order}
					Update Payment Order
				{:else}
					Create Payment Order
				{/if}
			</h3>
			<button
				on:click={close}
				class="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="w-6 h-6"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Body -->
		<div class="py-4 space-y-4">
			<div>
				<label for="user" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					User
				</label>
				<select
					id="user"
					bind:value={selectedUserId}
					disabled={order?.user_id}
					class="mt-1 block w-full py-2 px-3 border disabled:opacity-50 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				>
					<option value="" disabled>Select a user</option>
					{#each users as user}
						<option value={user.id}>{user.name} ({user.email})</option>
					{/each}
				</select>
			</div>

			<div>
				<label for="orderType" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					Order Type
				</label>
				<select
					id="orderType"
					bind:value={orderType}
					class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				>
					<option value="manual">Manual</option>
					<option value="credit">Credit</option>
					<option value="plan_payment">Plan Payment</option>
					<option value="upgrade">Upgrade</option>
				</select>
			</div>

			<div>
				<label for="planId" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					Plan
				</label>
				<select
					id="planId"
					bind:value={planId}
					class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				>
					<option value="free">Free</option>
					<option value="starter">Starter</option>
					<option value="pro">Pro</option>
					<option value="studio">Studio</option>
				</select>
			</div>

                        <div>
                                <label for="credits" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Credits
                                </label>
                                <input
                                        type="number"
                                        id="credits"
                                        bind:value={credits}
                                        class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                />
                        </div>

                        <div>
                                <label for="imageCredits" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Image Credits
                                </label>
                                <input
                                        type="number"
                                        id="imageCredits"
                                        bind:value={imageCredits}
                                        class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                />
                        </div>

                        <div>
                                <label for="videoCredits" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Video Credits
                                </label>
                                <input
                                        type="number"
                                        id="videoCredits"
                                        bind:value={videoCredits}
                                        class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                />
                        </div>

			<div>
				<label for="amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					Amount
				</label>
				<input
					type="number"
					id="amount"
					bind:value={amount}
					class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				/>
			</div>

			<div>
				<label for="provider" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					Provider
				</label>
				<input
					type="text"
					id="provider"
					bind:value={provider}
					class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				/>
			</div>

			<div>
				<label for="notes" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					Notes
				</label>
				<textarea
					id="notes"
					bind:value={notes}
					rows="3"
					class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				></textarea>
			</div>
		</div>

		<!-- Footer -->
		<div class="flex justify-end pt-4 border-t dark:border-gray-700">
			<button
				on:click={close}
				class="mr-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
			>
				Cancel
			</button>
			<button
				on:click={handleSubmit}
				class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 border border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
			>
				{#if order}
					Update
				{:else}
					Create
				{/if}
			</button>
		</div>
	</div>
</Modal>
