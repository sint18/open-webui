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

export const checkPendingOrders = async (token: string) => {
	try {
		const orders = await getPaymentOrders(token, 0, 10); // Get latest 10 orders
		return orders.some((order: { status: string }) => order.status === 'pending');
	} catch (error) {
		console.error('Failed to check pending orders:', error);
		return false; // Return false if unable to check
	}
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

// Admin: Get all payment orders across all users
export const getAllPaymentOrders = async (
	token: string,
	skip = 0,
	limit = 50,
	status?: string,
	userEmail?: string
) => {
	const params = new URLSearchParams({
		skip: skip.toString(),
		limit: limit.toString()
	});

	if (status) params.append('status', status);
	if (userEmail) params.append('user_email', userEmail);

	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/admin/orders?${params.toString()}`, {
		headers: {
			Authorization: `Bearer ${token}`
		}
	});

	if (!response.ok) {
		throw new Error('Failed to fetch all orders');
	}
	return response.json();
};

export const confirmPaymentOrder = async (token: string, orderId: string) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/admin/orders/${orderId}/confirm`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!response.ok) {
		if (response.status === 409) {
			// Handle conflict status (order already processed)
			const errorData = await response
				.json()
				.catch(() => ({ detail: 'Order has already been processed' }));
			throw new Error(errorData.detail || 'Order has already been processed');
		}
		throw new Error('Failed to confirm payment order');
	}
	return response.json();
};

export const declinePaymentOrder = async (token: string, orderId: string) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/admin/orders/${orderId}/decline`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!response.ok) {
		if (response.status === 409) {
			// Handle conflict status (order already processed)
			const errorData = await response
				.json()
				.catch(() => ({ detail: 'Order has already been processed' }));
			throw new Error(errorData.detail || 'Order has already been processed');
		}
		throw new Error('Failed to decline payment order');
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

export const createManualPaymentOrder = async (token: string, order: any) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/admin/orders`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(order)
	});
	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}
	return response.json();
};

export const updatePaymentOrder = async (token: string, orderId: string, order: any) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/billing/admin/orders/${orderId}`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(order)
	});
	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}
	return response.json();
};