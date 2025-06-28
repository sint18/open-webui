<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	/**
	 * MMK pricing table. Update amounts whenever you change your price.
	 */
	const PLAN_PRESETS = {
		starter: { label: 'Starter', amount_mmk: 30000 },
		pro: { label: 'Pro', amount_mmk: 55000 },
		studio: { label: 'Studio', amount_mmk: 125000 }
	} as const;

	// Extract plan from query string – fallback to starter
	$: planId = ($page.url.searchParams.get('plan') as keyof typeof PLAN_PRESETS) ?? 'starter';
	$: plan = PLAN_PRESETS[planId] ?? PLAN_PRESETS.starter;

	// Form state
	let provider = '';
	let file: File | null = null;
	let submitting = false;

	function handleFileChange(e: Event) {
		const tgt = e.target as HTMLInputElement;
		file = tgt.files?.[0] ?? null;
	}

	async function submit() {
		if (!provider || !file) {
			toast.error('Please select a provider and upload your payment screenshot.');
			return;
		}

		submitting = true;

		const form = new FormData();
		form.append('type', 'plan_payment');
		form.append('plan_id', planId);
		form.append('amount_mmk', plan.amount_mmk.toString());
		form.append('provider', provider);
		form.append('screenshot', file);

		try {
			const res = await fetch('/api/v1/billing/orders', {
				method: 'POST',
				body: form,
				credentials: 'include' // ensures cookie‑based auth is sent
			});

			if (!res.ok) {
				throw new Error(await res.text());
			}

			toast.success('Payment submitted! We will verify and activate your plan soon.');
			goto('/home');
		} catch (err) {
			toast.error(`Failed to submit payment: ${err}`);
		} finally {
			submitting = false;
		}
	}
</script>

<section class="max-w-md mx-auto py-12 px-4 sm:px-6 lg:px-8">
	<h1 class="text-center text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
		{plan.label} Plan
	</h1>
	<p class="text-center text-gray-700 dark:text-gray-300 mb-8">
		Amount to pay: <span class="font-semibold">MMK {plan.amount_mmk.toLocaleString()}</span>
	</p>

	<div class="space-y-6">
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

		<div>
			<label
				for="payment-screenshot"
				class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
			>
				Payment screenshot
			</label>
			<input
				id="payment-screenshot"
				type="file"
				accept="image/*"
				class="block w-full text-sm text-gray-900 dark:text-gray-100
			   file:mr-4 file:py-2 file:px-4
			   file:rounded-xl file:border-0
			   file:text-sm file:font-semibold
			   file:bg-primary-600 file:text-white
			   hover:file:bg-primary-700
			   dark:file:bg-primary-500 dark:hover:file:bg-primary-400"
				on:change={handleFileChange}
			/>
		</div>

		<button
			class="w-full inline-flex items-center justify-center rounded-xl px-4 py-2 font-medium
             text-foreground bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500
             dark:bg-primary-500 dark:hover:bg-primary-400 disabled:opacity-50"
			on:click|preventDefault={submit}
			disabled={submitting || !provider || !file}
		>
			{submitting ? 'Submitting…' : 'Pay'}
		</button>
	</div>
</section>

<style>
	/* Tailwind handles most styling */
</style>
