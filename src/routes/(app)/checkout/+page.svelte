<script lang="ts">
	import { onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	// Get user token from localStorage
	let token = '';
	if (typeof localStorage !== 'undefined') {
		token = localStorage.getItem('token') || '';
	}

	// --- plan table -----------------------------------------------------------
	const PLAN_PRESETS = {
		starter: { label: 'Starter', amount_mmk: 30000, credits: 750 },
		pro: { label: 'Pro', amount_mmk: 55000, credits: 1500 },
		studio: { label: 'Studio', amount_mmk: 125000, credits: 4500 }
	} as const;

	// --- reactive plan lookup --------------------------------------------------
	$: planId = ($page.url.searchParams.get('plan') ?? 'starter') as keyof typeof PLAN_PRESETS;
	$: currentPlan = PLAN_PRESETS[planId] ?? PLAN_PRESETS.starter;

	// --- form state ------------------------------------------------------------
	let provider: 'kpay' | 'wavepay' | '' = '';
	let screenshotFile: File | null = null;
	let previewUrl: string | null = null;
	let submitting = false;

	function onFileChange(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0] ?? null;
		if (previewUrl) URL.revokeObjectURL(previewUrl); // cleanup old preview
		screenshotFile = file;
		previewUrl = file ? URL.createObjectURL(file) : null;
	}

	onDestroy(() => {
		if (previewUrl) URL.revokeObjectURL(previewUrl);
	});

	// --- submit ---------------------------------------------------------------
	async function submit() {
		if (!provider) {
			toast.error('Please select a payment provider');
			return;
		}
		if (!screenshotFile) {
			toast.error('Please upload the payment screenshot');
			return;
		}

		submitting = true;

		// Create URL with query parameters for the form data
		const url = new URL(`${WEBUI_API_BASE_URL}/billing/orders`);
		url.searchParams.append('type', 'plan_payment');
		url.searchParams.append('plan_id', planId);
		url.searchParams.append('amount_mmk', currentPlan.amount_mmk.toString());
		url.searchParams.append('credits', currentPlan.credits.toString());
		url.searchParams.append('provider', provider);

		// Create FormData only for the file
		const formData = new FormData();
		formData.append('screenshot', screenshotFile);
		try {
			const res = await fetch(url.toString(), {
				method: 'POST',
				headers: {
					Accept: 'application/json',
					Authorization: `Bearer ${token}`
				},
				body: formData,
				credentials: 'include'
			});

			if (!res.ok) {
				const msg = await res.text();
				throw new Error(msg || 'Payment submission failed');
			}

			toast.success("Payment submitted! We'll verify shortly.");
			goto('/pricing', { replaceState: true });
		} catch (err) {
			toast.error(err instanceof Error ? err.message : String(err));
			console.error('Payment submission error:', err);
		} finally {
			submitting = false;
		}
	}
</script>

<section class="w-full flex justify-center py-12 px-4">
	<div class="w-full max-w-lg">
		<!-- Plan summary -->
		<h1 class="text-center text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
			{currentPlan.label} Plan
		</h1>
		<p class="text-center text-gray-600 dark:text-gray-400 mb-8">
			Amount to pay: <span class="font-semibold text-gray-900 dark:text-white"
				>MMK {currentPlan.amount_mmk.toLocaleString()}</span
			>
		</p>

		<form on:submit|preventDefault={submit} class="space-y-6">
			<!-- Provider select -->
			<div>
				<label
					for="payment-provider"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
				>
					Payment provider
				</label>
				<select
					id="payment-provider"
					class="block w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
					bind:value={provider}
				>
					<option value="" disabled selected>Select …</option>
					<option value="kpay">KPay</option>
					<option value="wavepay">Wave Pay</option>
				</select>
			</div>

			<!-- Screenshot upload with drag‑n‑drop feel -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>Payment screenshot</label
				>
				<label
					for="screenshot"
					class="flex flex-col items-center justify-center px-4 py-8 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400"
				>
					{#if previewUrl}
						<img
							src={previewUrl}
							alt="Screenshot preview"
							class="max-h-48 object-contain rounded-md"
						/>
						<span class="mt-2 text-sm">Click to replace</span>
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							fill="currentColor"
							class="w-10 h-10 mb-3"
						>
							<path
								d="M12 16.5l3-3 2.3 2.3 4.7-4.8 1 1-5.7 5.7L15 14.5l-3 3-6-6L8 9l4 4 3-3 4 4-1 1-3-3-3 3-4-4L3 11l9 9z"
							/>
						</svg>
						<p class="text-sm">Click to upload PNG/JPEG (max 5 MB)</p>
					{/if}
					<input
						id="screenshot"
						type="file"
						accept="image/*"
						on:change={onFileChange}
						class="hidden"
						required
					/>
				</label>
			</div>

			<!-- Submit button -->
			<button
				type="submit"
				class="w-full bg-gray-900 hover:bg-gray-800 dark:bg-gray-100 dark:hover:bg-gray-200 dark:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed text-white transition rounded-xl px-4 py-3 font-medium focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400"
				disabled={submitting}
			>
				{submitting ? 'Submitting…' : 'Pay Now'}
			</button>
		</form>
	</div>
</section>

<style>
	/* rely on Tailwind for utility classes */
</style>
