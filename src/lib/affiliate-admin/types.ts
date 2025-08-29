export type DecimalString = string;

export interface AuditLog {
    id: string;
    actor_id: string;
    resource: string;
    action: string;
    before?: Record<string, any> | null;
    after?: Record<string, any> | null;
    reason?: string | null;
    timestamp: number;
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
    terms_version?: string;
    audit_logs: AuditLog[];
}

export interface Application {
    id: string;
    partner_id: string;
    name?: string;
    email?: string;
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

export interface PayoutItem {
    id: string;
    payout_id: string;
    commission_id: string;
    amount: DecimalString;
    created_at: number;
}

export interface Payout {
    id: string;
    partner_id: string;
    requested_amount: DecimalString;
    total_amount: DecimalString;
    fee_mmk: DecimalString;
    status: 'pending' | 'approved' | 'paid' | 'rejected';
    reference?: string;
    approved_mmk?: DecimalString;
    created_at: number;
}

export interface PayoutDetail extends Payout {
    items: PayoutItem[];
}

export interface Coupon {
    id: string;
    partner_id: string;
    code: string;
    discount_percent?: number;
    expires_at?: number;
    active: boolean;
    created_at: number;
}

export interface Click {
    id: number;
    partner_id: string;
    link_id?: string;
    coupon_id?: string;
    user_agent?: string;
    created_at: number;
}

export interface Attribution {
    id: string;
    click_id: number;
    partner_id: string;
    attr_via: string;
    created_at: number;
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
