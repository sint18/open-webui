<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { checkPendingOrders } from '$lib/apis/billing';
	import { trackEvent, ANALYTICS_EVENTS } from '$lib/utils/analytics';

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
	$: finalAmount = currentPlan?.amount_mmk ?? PLAN_PRESETS.starter.amount_mmk;

	// --- discount code state ---------------------------------------------------
	let step: 'discount' | 'payment' = 'discount';
	let discountCode = '';
	let discountCodeValid = false;
	let discountValidating = false;
	let appliedDiscount: { code: string; percent: number } | null = null;

	// --- payment form state ----------------------------------------------------
	let provider: 'kpay' | 'wavepay' | '' = '';
	let screenshotFile: File | null = null;
	let previewUrl: string | null = null;
	let submitting = false;
	let hasPendingOrder = false;

	// Track payment provider selection
	$: if (provider) {
		trackEvent(ANALYTICS_EVENTS.CHECKOUT_PAYMENT_PROVIDER_SELECTED, {
			provider: provider,
			plan_id: planId,
			plan_amount: finalAmount
		});
	}

	// Check for pending orders on mount
	onMount(async () => {
		// Track checkout page visit
		trackEvent(ANALYTICS_EVENTS.CHECKOUT_PAGE_VISITED, {
			plan_id: planId,
			plan_amount: finalAmount,
			referrer: document.referrer
		});

		if (token) {
			hasPendingOrder = await checkPendingOrders(token);
		}
	});

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

	// --- payment details ---------------------------------------------------
	const paymentDetails = {
		kpay: {
			name: 'Zaw Htike Aung',
			phone: '09777541818'
		},
		wavepay: {
			name: 'Zaw Htike Aung',
			phone: '09777541818'
		}
	};

	// --- discount validation ---------------------------------------------------
	async function validateDiscountCode() {
		if (!discountCode.trim()) {
			toast.error('Please enter a discount code');
			return;
		}

		discountValidating = true;
		discountCodeValid = false;

		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/discount/validate/${discountCode}`, {
				method: 'GET',
				headers: {
					Accept: 'application/json',
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || 'Invalid discount code');
			}

			const validationResult = await response.json();

			if (validationResult.valid) {
				discountCodeValid = true;
				appliedDiscount = {
					code: discountCode,
					percent: validationResult.discount_percent
				};

				// Calculate the discounted amount
				const discountAmount = (currentPlan.amount_mmk * appliedDiscount.percent) / 100;
				finalAmount = currentPlan.amount_mmk - discountAmount;

				// Track discount code application
				trackEvent(ANALYTICS_EVENTS.CHECKOUT_DISCOUNT_APPLIED, {
					discount_code: discountCode,
					discount_percent: validationResult.discount_percent,
					plan_id: planId,
					original_amount: currentPlan.amount_mmk,
					final_amount: finalAmount,
					savings: discountAmount
				});

				toast.success(`Discount code applied: ${appliedDiscount.percent}% off`);
			} else {
				throw new Error(validationResult.message || 'Invalid discount code');
			}
		} catch (error) {
			discountCodeValid = false;
			appliedDiscount = null;
			finalAmount = currentPlan.amount_mmk;
			toast.error(error instanceof Error ? error.message : 'Failed to validate discount code');
		} finally {
			discountValidating = false;
		}
	}

	// Add this function to your script section
	async function copyToClipboard(text: string) {
		try {
			await navigator.clipboard.writeText(text);
			toast.success('Phone number copied to clipboard!');
		} catch (err) {
			console.error('Failed to copy: ', err);
			toast.error('Failed to copy phone number');
		}
	}

	function continueWithoutDiscount() {
		step = 'payment';
		appliedDiscount = null;
		finalAmount = currentPlan.amount_mmk;
	}

	function continueWithDiscount() {
		if (!discountCodeValid || !appliedDiscount) {
			toast.error('Please enter a valid discount code first');
			return;
		}
		step = 'payment';
	}

	// --- payment submission ----------------------------------------------------
	async function submit() {
		if (!provider) {
			toast.error('Please select a payment provider');
			return;
		}
		if (!screenshotFile) {
			toast.error('Please upload the payment screenshot');
			return;
		}

		// Check for pending orders before submission
		if (hasPendingOrder) {
			toast.error(
				'You already have a pending payment order. Please wait for it to be processed before submitting another.'
			);
			return;
		}

		submitting = true;

		try {
			// Track payment submission
			trackEvent(ANALYTICS_EVENTS.CHECKOUT_PAYMENT_SUBMITTED, {
				plan_id: planId,
				plan_amount: finalAmount,
				provider: provider,
				has_discount: !!appliedDiscount,
				discount_code: appliedDiscount?.code || null,
				discount_percent: appliedDiscount?.percent || null
			});

			// Create FormData for the file and form fields
			const formData = new FormData();
			formData.append('type', 'plan_payment');
			formData.append('plan_id', planId);
			formData.append('amount_mmk', currentPlan.amount_mmk.toString());
			formData.append('credits', currentPlan.credits.toString());
			formData.append('provider', provider);
			formData.append('screenshot', screenshotFile);

			// If we have a valid discount code, include it
			if (appliedDiscount) {
				formData.append('discount_code', appliedDiscount.code);
			}

			const res = await fetch(`${WEBUI_API_BASE_URL}/billing/orders`, {
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

			// Track successful payment submission
			trackEvent(ANALYTICS_EVENTS.CHECKOUT_PAYMENT_SUCCESS, {
				plan_id: planId,
				plan_amount: finalAmount,
				provider: provider,
				has_discount: !!appliedDiscount,
				discount_code: appliedDiscount?.code || null,
				discount_percent: appliedDiscount?.percent || null
			});

			toast.success("Payment submitted! We'll verify shortly.");
			goto('/pricing', { replaceState: true });
		} catch (err) {
			// Track failed payment submission
			trackEvent(ANALYTICS_EVENTS.CHECKOUT_PAYMENT_FAILED, {
				plan_id: planId,
				plan_amount: finalAmount,
				provider: provider,
				has_discount: !!appliedDiscount,
				discount_code: appliedDiscount?.code || null,
				discount_percent: appliedDiscount?.percent || null,
				error: err instanceof Error ? err.message : String(err)
			});

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

		{#if hasPendingOrder}
			<div
				class="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg"
			>
				<div class="flex items-center">
					<svg
						class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2"
						fill="currentColor"
						viewBox="0 0 20 20"
					>
						<path
							fill-rule="evenodd"
							d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
							clip-rule="evenodd"
						></path>
					</svg>
					<div>
						<p class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
							You have a pending payment order
						</p>
						<p class="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
							Please wait for your current order to be processed before submitting another.
						</p>
					</div>
				</div>
			</div>
		{/if}

		{#if step === 'discount'}
			<!-- Discount code step -->
			<p class="text-center text-gray-600 dark:text-gray-400 mb-8">
				Original amount: <span class="font-semibold text-gray-900 dark:text-white">
					MMK {currentPlan.amount_mmk.toLocaleString()}
				</span>
			</p>

			<div class="space-y-6">
				<div>
					<label
						for="discount-code"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>
						Discount code (optional)
					</label>
					<div class="flex space-x-2">
						<input
							id="discount-code"
							type="text"
							placeholder="Enter discount code"
							class="flex-grow rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
							bind:value={discountCode}
							disabled={discountValidating || discountCodeValid}
						/>
						<button
							type="button"
							class="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:text-gray-200 text-white rounded-xl px-4 py-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
							on:click={validateDiscountCode}
							disabled={discountValidating || discountCodeValid || !discountCode.trim()}
						>
							{#if discountValidating}
								Validating...
							{:else if discountCodeValid}
								Applied
							{:else}
								Apply
							{/if}
						</button>
					</div>
				</div>

				{#if appliedDiscount}
					<div
						class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900 rounded-lg p-4"
					>
						<div class="flex items-start">
							<div class="flex-shrink-0">
								<svg
									class="h-5 w-5 text-green-600 dark:text-green-400"
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
										clip-rule="evenodd"
									/>
								</svg>
							</div>
							<div class="ml-3">
								<h3 class="text-sm font-medium text-green-800 dark:text-green-200">
									Discount applied!
								</h3>
								<div class="mt-2 text-sm text-green-700 dark:text-green-300">
									<p>You'll receive a {appliedDiscount.percent}% discount.</p>
									<p class="font-medium mt-1">
										New amount: MMK {finalAmount.toLocaleString()}
									</p>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<div class="flex gap-3 pt-2 flex-col md:flex-row">
					<button
						type="button"
						class="inline-flex disabled:text-gray-600 disabled:opacity-50 items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus-visible:ring-2 focus-visible:ring-primary-500 focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400"
						on:click={continueWithDiscount}
						disabled={!discountCodeValid}
					>
						Continue
					</button>
					<button
						type="button"
						class="inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus-visible:ring-2 focus-visible:ring-primary-500 focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400"
						on:click={continueWithoutDiscount}
					>
						Continue without discount
					</button>
				</div>
			</div>
		{:else}
			<!-- Payment form step -->
			<p class="text-center text-gray-600 dark:text-gray-400 mb-8">
				Amount to pay: <span class="font-semibold text-gray-900 dark:text-white">
					MMK {finalAmount.toLocaleString()}
				</span>
				{#if appliedDiscount}
					<span class="ml-2 text-sm text-green-600 dark:text-green-400">
						({appliedDiscount.percent}% discount applied)
					</span>
				{/if}
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

				<!-- Payment details -->
				{#if provider}
					<div
						class="bg-blue-50 dark:bg-blue-900/20 border border-teal-200 dark:border-teal-900 rounded-lg p-4"
					>
						<h3 class="text-sm font-medium text-teal-800 dark:text-blue-200 mb-3">
							Payment Details
						</h3>
						<div class="space-y-2 text-sm text-teal-700 dark:text-teal-300">
							{#if provider === 'kpay'}
								<div class="flex justify-between">
									<span class="font-medium">KBZ Pay Name:</span>
									<span>{paymentDetails.kpay.name}</span>
								</div>
								<div class="flex justify-between">
									<span class="font-medium">KBZ Pay Phone:</span>

									<div class="flex items-center gap-2">
										<button
											type="button"
											on:click={() => copyToClipboard(paymentDetails.kpay.phone)}
											class="p-1 text-teal-600 hover:text-teal-800 dark:text-blue-400 dark:hover:text-teal-200 transition-colors"
											title="Copy phone number"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2"
											>
												<rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
												<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
											</svg>
										</button>
										<span>{paymentDetails.kpay.phone}</span>
									</div>
								</div>
							{:else if provider === 'wavepay'}
								<div class="flex justify-between">
									<span class="font-medium">Wave Pay Name:</span>
									<span>{paymentDetails.wavepay.name}</span>
								</div>
								<div class="flex justify-between">
									<span class="font-medium">Wave Pay Phone:</span>
									<div class="flex items-center gap-2">
										<button
											type="button"
											on:click={() => copyToClipboard(paymentDetails.wavepay.phone)}
											class="p-1 text-teal-600 hover:text-teal-800 dark:text-blue-400 dark:hover:text-teal-200 transition-colors"
											title="Copy phone number"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												stroke-width="2"
											>
												<rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
												<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
											</svg>
										</button>
										<span>{paymentDetails.wavepay.phone}</span>
									</div>
								</div>
							{/if}
						</div>
						<div
							class="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-900 rounded-md"
						>
							<p class="text-xs text-yellow-700 dark:text-yellow-300">
								Please send the payment to the above details and upload the screenshot below.
							</p>
						</div>
					</div>
				{/if}

				<!-- Screenshot upload with drag‑n‑drop feel -->
				<div>
					<p class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Payment screenshot
					</p>
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
					class="w-full bg-gray-900 hover:bg-gray-800 dark:bg-gray-100 dark:hover:bg-gray-200 dark:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed text-white transition rounded-xl px-4 py-2 font-medium focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400"
					disabled={submitting || hasPendingOrder}
				>
					{submitting ? 'Submitting…' : hasPendingOrder ? 'Order Pending' : 'Pay Now'}
				</button>
			</form>
		{/if}
	</div>
</section>

<style>
	/* rely on Tailwind for utility classes */
</style>
