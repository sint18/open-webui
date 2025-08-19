import { writable } from 'svelte/store';
import type {
    AffiliateSettings,
    PartnerDetail,
    TableState,
} from './types';
import { getSettings, getPartner } from './api';

// Table states for various admin views
export const applicationsTable = writable<TableState>({ page: 1 });
export const partnersTable = writable<TableState>({ page: 1 });
export const commissionsTable = writable<TableState>({ page: 1 });
export const linksTable = writable<TableState>({ page: 1 });

// Affiliate program settings cache
export const affiliateSettings = writable<AffiliateSettings | null>(null);
let settingsFetchedAt = 0;
const SETTINGS_TTL = 5 * 60 * 1000; // 5 minutes

export const fetchAffiliateSettings = async (token: string) => {
    const now = Date.now();
    if (now - settingsFetchedAt < SETTINGS_TTL && settingsFetchedAt !== 0) {
        return;
    }
    const data = await getSettings(token);
    affiliateSettings.set(data);
    settingsFetchedAt = now;
};

// Partner detail lookup cache with TTL
const partnerCache = new Map<string, { data: PartnerDetail; ts: number }>();
const PARTNER_TTL = 60 * 1000; // 1 minute

export const getPartnerCached = async (
    token: string,
    id: string
): Promise<PartnerDetail> => {
    const now = Date.now();
    const cached = partnerCache.get(id);
    if (cached && now - cached.ts < PARTNER_TTL) {
        return cached.data;
    }
    const data = await getPartner(token, id);
    partnerCache.set(id, { data, ts: now });
    return data;
};

export const clearPartnerCache = () => partnerCache.clear();
