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
    const response = await fetch(`${WEBUI_API_BASE_URL}/billing/credits/${userId}`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
    if (!response.ok) throw new Error('Failed to fetch user credits');
    return response.json();
};

export const getTransactions = async (token: string, skip = 0, limit = 50) => {
    const response = await fetch(
        `${WEBUI_API_BASE_URL}/billing/transactions?skip=${skip}&limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
    if (!response.ok) throw new Error('Failed to fetch transactions');
    return response.json();
};

export const getPaymentOrders = async (token: string, skip = 0, limit = 50) => {
    const response = await fetch(
        `${WEBUI_API_BASE_URL}/billing/orders?skip=${skip}&limit=${limit}`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
    if (!response.ok) throw new Error('Failed to fetch payment orders');
    return response.json();
};