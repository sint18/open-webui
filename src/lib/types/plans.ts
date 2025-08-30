export type PlanType = 'subscription' | 'package' | 'topup' | 'custom';

export interface Plan {
    id: string;
    name: string;
    description?: string;
    price: number;
    credits: number;
    plan_type: PlanType;
    features?: Record<string, unknown>;
    is_active: boolean;
    created_at: number;
    updated_at: number;
}
