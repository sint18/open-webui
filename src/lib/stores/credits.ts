import { writable, derived } from 'svelte/store';
import { getUserCredits } from '$lib/apis/billing';

export interface UserCredits {
	user_id: string;
	plan_id: string;
	credit_balance: number;
	monthly_quota: number;
	current_period_end?: number;
	status: 'active' | 'grace' | 'expired';
	updated_at: number;
}

export interface CreditUsageInfo {
	used: number;
	limit: number;
	percent: number;
}

// Credit store
export const userCredits = writable<UserCredits | null>(null);
export const creditsLoading = writable<boolean>(false);
export const creditsError = writable<string | null>(null);

// Last credit usage info from chat responses
export const lastCreditUsage = writable<CreditUsageInfo | null>(null);

// Track when we last showed low credit toast
let lastLowCreditToastTime = 0;
const TOAST_COOLDOWN = 60 * 60 * 1000; // 1 hour

// Derived stores for computed values
export const creditPercentage = derived(userCredits, ($credits) => {
	if (!$credits || $credits.monthly_quota <= 0) return 0;
	return Math.max(0, Math.min(100, ($credits.credit_balance / $credits.monthly_quota) * 100));
});

export const isCreditsLow = derived(creditPercentage, ($percentage) => $percentage < 20);

export const isCreditsCritical = derived(creditPercentage, ($percentage) => $percentage < 10);

// Function to update credit usage from chat responses
export const updateCreditUsage = (usage: CreditUsageInfo) => {
	lastCreditUsage.set(usage);

	// Update user credits based on usage info
	if (usage.limit > 0) {
		const credit_balance = usage.limit - usage.used;
		userCredits.update((current) => {
			if (current) {
				return {
					...current,
					credit_balance: credit_balance
				};
			}
			return current;
		});
	}

	// Check if we should show low credit toast
	if (usage.percent >= 80) {
		// 20% remaining = 80% used
		const now = Date.now();
		// if (now - lastLowCreditToastTime > TOAST_COOLDOWN) {
		lastLowCreditToastTime = now;
		showLowCreditToast(usage);
		// }
	}

	// Reset toast timer if credits go back above 80%
	if (usage.percent < 80) {
		lastLowCreditToastTime = 0;
	}
};

const showLowCreditToast = (usage: CreditUsageInfo) => {
	// Dispatch a custom event that the toast component will listen for
	const event = new CustomEvent('low-credit-warning', {
		detail: {
			remaining: 100 - usage.percent,
			used: usage.used,
			limit: usage.limit,
			percent: usage.percent
		}
	});
	window.dispatchEvent(event);
};

// Cache with timestamp to avoid duplicate calls
let lastFetch = 0;
const CACHE_DURATION = 30 * 1000; // 30 seconds

// Actions
export const fetchUserCredits = async (token: string) => {
	if (!token) return;

	const now = Date.now();
	if (now - lastFetch < CACHE_DURATION) {
		return; // Use cached data
	}

	creditsLoading.set(true);
	creditsError.set(null);
	lastFetch = now;

	try {
		const credits = await getUserCredits(token);
		userCredits.set(credits);
	} catch (error) {
		console.warn('Could not fetch user credits:', error);
		creditsError.set(error instanceof Error ? error.message : 'Failed to fetch credits');
		userCredits.set(null);
	} finally {
		creditsLoading.set(false);
	}
};

// Helper to refresh credits after successful payment
export const refreshCreditsAfterPayment = async (token: string) => {
	lastFetch = 0; // Reset cache
	await fetchUserCredits(token);
};
