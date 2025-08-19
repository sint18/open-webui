export type DecimalString = string;

export interface AuditLog {
    id: string;
    action: string;
    severity: 'info' | 'warning' | 'critical';
    details?: Record<string, any>;
    created_at: number;
}

export interface Partner {
    id: string;
    name: string;
    email: string;
    role: string;
    status?: 'active' | 'inactive' | 'suspended';
    balance: DecimalString;
}

export interface PartnerDetail extends Partner {
    payout_method?: string;
    payout_details?: Record<string, any>;
    rates?: Record<string, any>;
    audit_logs: AuditLog[];
}

export interface Application {
    id: string;
    partner_id: string;
    status: 'pending' | 'approved' | 'rejected';
    notes?: string;
    created_at: number;
    updated_at: number;
    fraud_flags: string[];
}

export interface ApplicationApproveForm {
    link_code: string;
    link_url: string;
    coupon_code?: string;
    coupon_discount_percent?: number;
    coupon_expires_at?: number;
}

export interface ApplicationRejectForm {
    note: string;
}

export interface PartnerUpdateForm {
    name?: string;
    email?: string;
    status?: 'active' | 'inactive' | 'suspended';
    payout_method?: string;
    payout_details?: Record<string, any>;
    rates?: Record<string, any>;
    terms_version?: string;
    blocked_channels?: string[];
}

export interface Commission {
    id: string;
    partner_id: string;
    order_id: string;
    type: string;
    status: 'pending' | 'approved' | 'rejected' | 'paid';
    amount: DecimalString;
    created_at: number;
    note?: string;
    fraud_flags: string[];
}

export interface CommissionActionForm {
    note?: string;
}

export interface CommissionAdjustmentForm {
    amount: DecimalString;
    reason?: string;
}

export interface Link {
    id: string;
    partner_id: string;
    code: string;
    url: string;
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    utm_term?: string;
    utm_content?: string;
    active: boolean;
    created_at: number;
}

export interface LinkCreateForm {
    partner_id: string;
    code: string;
    url: string;
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    utm_term?: string;
    utm_content?: string;
    active?: boolean;
}

export interface LinkUpdateForm {
    code?: string;
    url?: string;
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    utm_term?: string;
    utm_content?: string;
    active?: boolean;
}

export interface RollupRow {
    partner_id: string;
    total: DecimalString;
}

export interface AffiliateSettings {
    commission_rules?: Record<string, any>;
    lock_period_days?: number;
    attribution_policy?: string;
    cookie_window_days?: number;
}

export interface AffiliateSettingsForm extends AffiliateSettings {}

export interface TableState {
    page: number;
    query?: string;
    status?: string;
    flagged?: boolean;
}
