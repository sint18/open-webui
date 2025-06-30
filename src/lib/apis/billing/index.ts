import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getUserCredits = async (token: string) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/credits`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	if (!response.ok) throw new Error('Failed to fetch user credits');
	return response.json();
};

export const getUserCreditsByUserId = async (token: string, userId: string) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/${userId}/credits`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});

	// Handle 404 gracefully - user may not have credit record yet
	if (response.status === 404) {
		return null;
	}

	if (!response.ok) {
		throw new Error('Failed to fetch user credits');
	}

	return response.json();
};

export const getTransactions = async (token: string, skip = 0, limit = 50) => {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/billing/transactions?skip=${skip}&limit=${limit}`,
		{
			headers: {
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!response.ok) throw new Error('Failed to fetch transactions');
	return response.json();
};

export const getTransactionsByUserId = async (
	token: string,
	userId: string,
	skip = 0,
	limit = 50
) => {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/billing/${userId}/transactions?skip=${skip}&limit=${limit}`,
		{
			headers: {
				Authorization: `Bearer ${token}`
			}
		}
	);

	// Handle 404 gracefully - user may not have transactions yet
	if (response.status === 404) {
		return [];
	}

	if (!response.ok) {
		throw new Error('Failed to fetch user transactions');
	}

	return response.json();
};

export const getPaymentOrders = async (token: string, skip = 0, limit = 50) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/orders?skip=${skip}&limit=${limit}`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});
	if (!response.ok) throw new Error('Failed to fetch payment orders');
	return response.json();
};

export const getPaymentOrdersByUserId = async (
	token: string,
	userId: string,
	skip = 0,
	limit = 50
) => {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/billing/${userId}/orders?skip=${skip}&limit=${limit}`,
		{
			headers: {
				Authorization: `Bearer ${token}`
			}
		}
	);
	if (!response.ok) {
		throw new Error('Failed to fetch user orders');
	}
	return await response.json();
};

export const confirmPaymentOrder = async (token: string, orderId: string) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/orders/confirm`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			order_id: orderId
		})
	});

	if (!response.ok) {
		throw new Error('Failed to confirm payment order');
	}
	return response.json();
};

// Admin: Create credit wallet for a user
export const createUserCredits = async (
	token: string,
	userId: string,
	planId: string,
	creditBalance: number,
	monthlyQuota: number,
	currentPeriodEnd?: number
) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/credits`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			user_id: userId,
			plan_id: planId,
			credit_balance: creditBalance,
			monthly_quota: monthlyQuota,
			current_period_end: currentPeriodEnd
		})
	});

	if (!response.ok) {
		throw new Error('Failed to create user credits');
	}
	return response.json();
};
