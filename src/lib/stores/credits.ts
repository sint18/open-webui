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

// Credit store
export const userCredits = writable<UserCredits | null>(null);
export const creditsLoading = writable<boolean>(false);
export const creditsError = writable<string | null>(null);

// Derived stores for computed values
export const creditPercentage = derived(userCredits, ($credits) => {
	if (!$credits || $credits.monthly_quota <= 0) return 0;
	return Math.max(0, Math.min(100, ($credits.credit_balance / $credits.monthly_quota) * 100));
});

export const isCreditsLow = derived(creditPercentage, ($percentage) => $percentage < 20);

export const isCreditsCritical = derived(creditPercentage, ($percentage) => $percentage < 10);

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
