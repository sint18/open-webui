declare global {
	interface Window {
		umami?: {
			track: (event: string, data?: Record<string, unknown>) => void;
		};
	}
}

export const trackEvent = (event: string, data?: Record<string, unknown>) => {
	if (typeof window !== 'undefined' && window.umami) {
		// Add timestamp and session info
		const enhancedData = {
			...data,
			timestamp: new Date().toISOString(),
			url: window.location.href
		};

		window.umami.track(event, enhancedData);
	}
};

export const ANALYTICS_EVENTS = {
	AUTH_SUCCESS: 'auth_success',
	FIRST_PROMPT_SENT: 'first_prompt_sent',
	MODEL_SELECTOR_CLICKED: 'model_selector_clicked',
	// Subscription flow events
	PRICING_PAGE_VISITED: 'pricing_page_visited',
	PRICING_PLAN_CLICKED: 'pricing_plan_clicked',
	PRICING_LINK_CLICKED: 'pricing_link_clicked',
	CHECKOUT_PAGE_VISITED: 'checkout_page_visited',
	CHECKOUT_DISCOUNT_APPLIED: 'checkout_discount_applied',
	CHECKOUT_PAYMENT_PROVIDER_SELECTED: 'checkout_payment_provider_selected',
	CHECKOUT_PAYMENT_SUBMITTED: 'checkout_payment_submitted',
	CHECKOUT_PAYMENT_SUCCESS: 'checkout_payment_success',
	CHECKOUT_PAYMENT_FAILED: 'checkout_payment_failed',
	SUBSCRIPTION_COMPLETED: 'subscription_completed'
} as const;
