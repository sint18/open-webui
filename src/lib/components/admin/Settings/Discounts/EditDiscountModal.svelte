<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		updateDiscountCode,
		type DiscountCode,
		type UpdateDiscountForm
	} from '$lib/apis/discounts';
	import Modal from '$lib/components/common/Modal.svelte';

	export let discount: DiscountCode;

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	let loading = false;
	let form: UpdateDiscountForm = {
		code: discount.code,
		discount_percent: discount.discount_percent,
		expiry_date: discount.expiry_date,
		usage_limit: discount.usage_limit,
		active: discount.active
	};

	// Validation
	let errors: Record<string, string> = {};

	function validateForm() {
		errors = {};

		if (!form.code?.trim()) {
			errors.code = 'Discount code is required';
		} else if (form.code.length < 3) {
			errors.code = 'Discount code must be at least 3 characters';
		} else if (!/^[A-Za-z0-9_-]+$/.test(form.code)) {
			errors.code = 'Discount code can only contain letters, numbers, hyphens, and underscores';
		}

		if (
			form.discount_percent !== undefined &&
			(form.discount_percent < 1 || form.discount_percent > 100)
		) {
			errors.discount_percent = 'Discount percentage must be between 1 and 100';
		}

		if (form.usage_limit !== null && form.usage_limit !== undefined && form.usage_limit < 1) {
			errors.usage_limit = 'Usage limit must be at least 1';
		}

		if (form.expiry_date) {
			const expiryDate = new Date(form.expiry_date);
			const today = new Date();
			today.setHours(0, 0, 0, 0);

			if (expiryDate <= today) {
				errors.expiry_date = 'Expiry date must be in the future';
			}
		}

		return Object.keys(errors).length === 0;
	}

	async function submitHandler() {
		if (!validateForm()) {
			return;
		}

		loading = true;
		try {
			// Convert empty strings to null for optional fields
			const submitData = {
				...form,
				code: form.code?.trim().toUpperCase(),
				expiry_date: form.expiry_date || null,
				usage_limit: form.usage_limit || null
			};

			await updateDiscountCode(localStorage.token, discount.id!, submitData);
			toast.success('Discount code updated successfully');
			dispatch('updated');
		} catch (error) {
			console.error('Failed to update discount code:', error);
			toast.error(typeof error === 'string' ? error : 'Failed to update discount code');
		} finally {
			loading = false;
		}
	}

	function closeModal() {
		dispatch('close');
	}

	// Auto-format expiry date
	function formatExpiryDate() {
		if (form.expiry_date) {
			const date = new Date(form.expiry_date);
			form.expiry_date = date.toISOString().split('T')[0];
		}
	}

	// Convert expiry_date to YYYY-MM-DD format for input
	$: if (discount.expiry_date && !form.expiry_date) {
		form.expiry_date = new Date(discount.expiry_date).toISOString().split('T')[0];
	}
</script>

<Modal size="md" on:close={closeModal}>
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
						d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
					></path>
				</svg>
				<span class="text-lg font-semibold text-gray-900 dark:text-white"
					>{$i18n.t('Edit Discount Code')}</span
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
		<form on:submit|preventDefault={submitHandler} class="space-y-4">
			<!-- Discount Code -->
			<div>
				<label for="code" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Discount Code')} *
				</label>
				<input
					id="code"
					type="text"
					bind:value={form.code}
					on:input={() => {
						if (form.code) {
							form.code = form.code.toUpperCase();
						}
						validateForm();
					}}
					placeholder="e.g. SAVE20"
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 {errors.code
						? 'border-red-500'
						: ''}"
					required
				/>
				{#if errors.code}
					<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.code}</p>
				{/if}
			</div>

			<!-- Discount Percentage -->
			<div>
				<label
					for="discount_percent"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Discount Percentage')} *
				</label>
				<div class="relative">
					<input
						id="discount_percent"
						type="number"
						min="1"
						max="100"
						bind:value={form.discount_percent}
						on:input={validateForm}
						class="w-full px-3 py-2 pr-8 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 {errors.discount_percent
							? 'border-red-500'
							: ''}"
						required
					/>
					<span class="absolute right-3 top-2 text-gray-500 dark:text-gray-400">%</span>
				</div>
				{#if errors.discount_percent}
					<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.discount_percent}</p>
				{/if}
			</div>

			<!-- Expiry Date -->
			<div>
				<label
					for="expiry_date"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Expiry Date')} ({$i18n.t('Optional')})
				</label>
				<input
					id="expiry_date"
					type="date"
					bind:value={form.expiry_date}
					on:change={formatExpiryDate}
					on:input={validateForm}
					min={new Date().toISOString().split('T')[0]}
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 {errors.expiry_date
						? 'border-red-500'
						: ''}"
				/>
				{#if errors.expiry_date}
					<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.expiry_date}</p>
				{/if}
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('Leave empty for no expiry date')}
				</p>
			</div>

			<!-- Usage Limit -->
			<div>
				<label
					for="usage_limit"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					{$i18n.t('Usage Limit')} ({$i18n.t('Optional')})
				</label>
				<input
					id="usage_limit"
					type="number"
					min="1"
					bind:value={form.usage_limit}
					on:input={validateForm}
					placeholder="e.g. 100"
					class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 {errors.usage_limit
						? 'border-red-500'
						: ''}"
				/>
				{#if errors.usage_limit}
					<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.usage_limit}</p>
				{/if}
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('Leave empty for unlimited usage')}
				</p>
			</div>

			<!-- Usage Information -->
			<div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					{$i18n.t('Usage Statistics')}
				</h4>
				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Times Used')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">{discount.used_count}</p>
					</div>
					<div>
						<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Created At')}</p>
						<p class="font-semibold text-gray-900 dark:text-white">
							{discount.created_at
								? new Date(discount.created_at * 1000).toLocaleDateString()
								: '-'}
						</p>
					</div>
				</div>
			</div>

			<!-- Active Status -->
			<div class="flex items-center space-x-2">
				<input
					id="active"
					type="checkbox"
					bind:checked={form.active}
					class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
				/>
				<label for="active" class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$i18n.t('Active')}
				</label>
			</div>
			<p class="text-xs text-gray-500 dark:text-gray-400 ml-6">
				{$i18n.t('Inactive codes cannot be used by customers')}
			</p>

			<!-- Buttons -->
			<div class="flex justify-end space-x-3 pt-4">
				<button
					type="button"
					on:click={closeModal}
					class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					{$i18n.t('Cancel')}
				</button>
				<button
					type="submit"
					disabled={loading}
					class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 border border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if loading}
						<svg class="animate-spin h-4 w-4 mr-2 inline" fill="none" viewBox="0 0 24 24">
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
						{$i18n.t('Updating...')}
					{:else}
						{$i18n.t('Update Discount Code')}
					{/if}
				</button>
			</div>
		</form>
	</div>
</Modal>
