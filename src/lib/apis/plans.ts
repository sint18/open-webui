import { WEBUI_API_BASE_URL } from '$lib/constants';
import { handle, jsonHeaders } from '$lib/utils/api-helper';

export const createPlan = async (token: string, plan: object) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/plans`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(plan),
    });
    return handle(res);
};

export const getPlans = async (token: string = '') => {
    const headers = token ? jsonHeaders(token) : undefined;
    const res = await fetch(`${WEBUI_API_BASE_URL}/plans`, {
        method: 'GET',
        headers,
    });
    return handle(res);
};

export const getPlanById = async (token: string = '', planId: string) => {
    const headers = token ? jsonHeaders(token) : undefined;
    const res = await fetch(`${WEBUI_API_BASE_URL}/plans/${planId}`, {
        method: 'GET',
        headers,
    });
    return handle(res);
};

export const updatePlan = async (token: string, planId: string, plan: object) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/plans/${planId}`, {
        method: 'PUT',
        headers: jsonHeaders(token),
        body: JSON.stringify(plan),
    });
    return handle(res);
};

export const deletePlan = async (token: string, planId: string) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/plans/${planId}`, {
        method: 'DELETE',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

