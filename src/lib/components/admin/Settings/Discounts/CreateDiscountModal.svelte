<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { createDiscountCode, type CreateDiscountForm } from '$lib/apis/discounts';
	import Modal from '$lib/components/common/Modal.svelte';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	let loading = false;
	let form: CreateDiscountForm = {
		code: '',
		discount_percent: 10,
		expiry_date: null,
		usage_limit: null,
		active: true
	};

	// Validation
	let errors: Record<string, string> = {};

	function validateForm() {
		errors = {};

		if (!form.code.trim()) {
			errors.code = 'Discount code is required';
		} else if (form.code.length < 3) {
			errors.code = 'Discount code must be at least 3 characters';
		} else if (!/^[A-Za-z0-9_-]+$/.test(form.code)) {
			errors.code = 'Discount code can only contain letters, numbers, hyphens, and underscores';
		}

		if (form.discount_percent < 1 || form.discount_percent > 100) {
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
				code: form.code.trim().toUpperCase(),
				expiry_date: form.expiry_date || null,
				usage_limit: form.usage_limit || null
			};

			await createDiscountCode(localStorage.token, submitData);
			toast.success('Discount code created successfully');
			dispatch('created');
		} catch (error) {
			console.error('Failed to create discount code:', error);
			toast.error(typeof error === 'string' ? error : 'Failed to create discount code');
		} finally {
			loading = false;
		}
	}

	function generateRandomCode() {
		const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
		let result = '';
		for (let i = 0; i < 8; i++) {
			result += chars.charAt(Math.floor(Math.random() * chars.length));
		}
		form.code = result;
		validateForm();
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
</script>

<Modal size="md" on:close={closeModal}>
	<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
		<div class="text-lg font-medium self-center flex items-center space-x-2">
			<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"
				></path>
			</svg>
			<span>{$i18n.t('Create Discount Code')}</span>
		</div>
		<button class="self-center" on:click={closeModal}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				class="w-5 h-5"
			>
				<path
					d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
				/>
			</svg>
		</button>
	</div>

	<div class="px-5 pb-4">
		<form on:submit|preventDefault={submitHandler} class="space-y-4">
			<!-- Discount Code -->
			<div>
				<label for="code" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Discount Code')} *
				</label>
				<div class="flex space-x-2">
					<input
						id="code"
						type="text"
						bind:value={form.code}
						on:input={() => {
							form.code = form.code.toUpperCase();
							validateForm();
						}}
						placeholder="e.g. SAVE20"
						class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 {errors.code
							? 'border-red-500'
							: ''}"
						required
					/>
					<button
						type="button"
						on:click={generateRandomCode}
						class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
					>
						{$i18n.t('Generate')}
					</button>
				</div>
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
						{$i18n.t('Creating...')}
					{:else}
						{$i18n.t('Create Discount Code')}
					{/if}
				</button>
			</div>
		</form>
	</div>
</Modal>
