import { WEBUI_API_BASE_URL } from '$lib/constants';
import { handle, jsonHeaders } from '$lib/utils/api-helper';

export const createQuotaPolicy = async (token: string, policy: object) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/quota_policies`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(policy),
    });
    return handle(res);
};

export const getQuotaPolicyById = async (token: string, policyId: string) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/quota_policies/${policyId}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const getQuotaPolicies = async (
    token: string,
    userId?: string,
    planId?: string,
) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (planId) params.append('plan_id', planId);
    const query = params.toString();
    const res = await fetch(
        `${WEBUI_API_BASE_URL}/quota_policies${query ? `?${query}` : ''}`,
        {
            method: 'GET',
            headers: jsonHeaders(token),
        },
    );
    return handle(res);
};

export const updateQuotaPolicy = async (
    token: string,
    policyId: string,
    policy: object,
) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/quota_policies/${policyId}`, {
        method: 'PUT',
        headers: jsonHeaders(token),
        body: JSON.stringify(policy),
    });
    return handle(res);
};

export const deleteQuotaPolicy = async (token: string, policyId: string) => {
    const res = await fetch(`${WEBUI_API_BASE_URL}/quota_policies/${policyId}`, {
        method: 'DELETE',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

