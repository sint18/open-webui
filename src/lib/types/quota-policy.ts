export type Window = '3h' | '12h' | 'day' | 'week' | 'month';

export interface QuotaPolicy {
    id: string;
    user_id?: string;
    plan_id?: string;
    resource_pattern: string;
    limit: number;
    window: Window;
    effective_from: number;
    expires_at?: number;
}
