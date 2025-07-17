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
	MODEL_SELECTOR_CLICKED: 'model_selector_clicked'
} as const;
