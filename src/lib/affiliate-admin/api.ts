import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
    Application,
    ApplicationApproveForm,
    ApplicationRejectForm,
    Partner,
    PartnerDetail,
    PartnerUpdateForm,
    Commission,
    CommissionActionForm,
    CommissionAdjustmentForm,
    Link,
    LinkCreateForm,
    LinkUpdateForm,
    RollupRow,
    AffiliateSettings,
    AffiliateSettingsForm,
} from './types';

const ADMIN_AFFILIATE_API_BASE_URL = `${WEBUI_API_BASE_URL}/admin/affiliate`;

const jsonHeaders = (token: string) => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
});

const handle = async (res: Response) => {
    if (!res.ok) {
        throw await res.json();
    }
    return res.json();
};

// Applications
export const listApplications = async (
    token: string,
    params: {
        status?: string;
        from?: number;
        to?: number;
        q?: string;
        page?: number;
        flagged?: boolean;
    } = {}
): Promise<Application[]> => {
    const query = new URLSearchParams();
    if (params.status) query.set('status', params.status);
    if (params.from) query.set('from', String(params.from));
    if (params.to) query.set('to', String(params.to));
    if (params.q) query.set('q', params.q);
    if (params.page) query.set('page', String(params.page));
    if (params.flagged) query.set('flagged', String(params.flagged));
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/applications?${query.toString()}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const getApplication = async (token: string, appId: string): Promise<Application> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/applications/${appId}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const approveApplication = async (
    token: string,
    appId: string,
    form: ApplicationApproveForm
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/applications/${appId}/approve`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const rejectApplication = async (
    token: string,
    appId: string,
    form: ApplicationRejectForm
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/applications/${appId}/reject`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const reviewApplicationFlags = async (
    token: string,
    appId: string
): Promise<{ id: string; flags_cleared: boolean }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/applications/${appId}/flags/review`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

// Partners
export const searchPartners = async (
    token: string,
    q?: string
): Promise<Partner[]> => {
    const query = q ? `?q=${encodeURIComponent(q)}` : '';
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/partners${query}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const getPartner = async (
    token: string,
    partnerId: string
): Promise<PartnerDetail> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/partners/${partnerId}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const updatePartner = async (
    token: string,
    partnerId: string,
    form: PartnerUpdateForm
): Promise<PartnerDetail> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/partners/${partnerId}`, {
        method: 'PUT',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const activatePartner = async (
    token: string,
    partnerId: string
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/partners/${partnerId}/activate`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const suspendPartner = async (
    token: string,
    partnerId: string
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/partners/${partnerId}/suspend`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

// Commissions
export const listCommissions = async (
    token: string,
    params: {
        status?: string;
        partner_id?: string;
        start?: number;
        end?: number;
        flagged?: boolean;
    } = {}
): Promise<Commission[]> => {
    const query = new URLSearchParams();
    if (params.status) query.set('status', params.status);
    if (params.partner_id) query.set('partner_id', params.partner_id);
    if (params.start) query.set('start', String(params.start));
    if (params.end) query.set('end', String(params.end));
    if (params.flagged) query.set('flagged', String(params.flagged));
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/commissions?${query.toString()}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const approveCommission = async (
    token: string,
    commissionId: string,
    form: CommissionActionForm
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/commissions/${commissionId}/approve`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const voidCommission = async (
    token: string,
    commissionId: string,
    form: CommissionActionForm
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/commissions/${commissionId}/void`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const adjustCommission = async (
    token: string,
    commissionId: string,
    form: CommissionAdjustmentForm
): Promise<{ id: string; adjustment: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/commissions/${commissionId}/adjust`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const reviewCommissionFlags = async (
    token: string,
    commissionId: string
): Promise<{ id: string; flags_cleared: boolean }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/commissions/${commissionId}/flags/review`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

// Payouts
export const approvePayout = async (
    token: string,
    payoutId: string
): Promise<{ id: string; status: string; approved_mmk: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/payouts/${payoutId}/approve`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const markPayoutPaid = async (
    token: string,
    payoutId: string
): Promise<{ id: string; status: string }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/payouts/${payoutId}/mark-paid`, {
        method: 'POST',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const exportPayouts = async (
    token: string
): Promise<string> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/payouts/export`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    if (!res.ok) {
        throw await res.json();
    }
    return res.text();
};

export const importPayouts = async (
    token: string,
    file: File
): Promise<{ imported: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/payouts/import`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });
    return handle(res);
};

// Links
export const listLinks = async (
    token: string,
    params: {
        partner_id?: string;
        active?: boolean;
        start?: number;
        end?: number;
    } = {}
): Promise<Link[]> => {
    const query = new URLSearchParams();
    if (params.partner_id) query.set('partner_id', params.partner_id);
    if (params.active !== undefined) query.set('active', String(params.active));
    if (params.start) query.set('start', String(params.start));
    if (params.end) query.set('end', String(params.end));
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/links?${query.toString()}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const createLink = async (
    token: string,
    form: LinkCreateForm
): Promise<Link> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/links`, {
        method: 'POST',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const updateLink = async (
    token: string,
    linkId: string,
    form: LinkUpdateForm
): Promise<Link> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/links/${linkId}`, {
        method: 'PATCH',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};

export const deleteLink = async (
    token: string,
    linkId: string
): Promise<{ id: string; deleted: boolean }> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/links/${linkId}`, {
        method: 'DELETE',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

// Reports & Settings
export const rollupReport = async (
    token: string,
    status?: string
): Promise<RollupRow[]> => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/reports/rollup${query}`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const getSettings = async (
    token: string
): Promise<AffiliateSettings> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/settings`, {
        method: 'GET',
        headers: jsonHeaders(token),
    });
    return handle(res);
};

export const updateSettings = async (
    token: string,
    form: AffiliateSettingsForm
): Promise<AffiliateSettings> => {
    const res = await fetch(`${ADMIN_AFFILIATE_API_BASE_URL}/settings`, {
        method: 'PUT',
        headers: jsonHeaders(token),
        body: JSON.stringify(form),
    });
    return handle(res);
};
