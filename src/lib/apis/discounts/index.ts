import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface DiscountCode {
	id?: string;
	code: string;
	discount_percent: number;
	expiry_date?: string | null;
	usage_limit?: number | null;
	used_count: number;
	is_active: boolean;
	created_at?: number;
	updated_at?: number;
}

export interface CreateDiscountForm {
	code: string;
	discount_percent: number;
	expiry_date?: string | null;
	usage_limit?: number | null;
	is_active?: boolean;
}

export interface UpdateDiscountForm {
	code?: string;
	discount_percent?: number;
	expiry_date?: string | null;
	usage_limit?: number | null;
	is_active?: boolean;
}

export interface DiscountUsage {
	id: string;
	user_id: string;
	discount_code_id: string;
	used_at: number;
	user_name?: string;
	user_email?: string;
}

// Admin: Create a new discount code
export const createDiscountCode = async (token: string, discount: CreateDiscountForm) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(discount)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Get all discount codes
export const getDiscountCodes = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Get discount code by ID
export const getDiscountCodeById = async (token: string, codeId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/${codeId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Get discount code by code value
export const getDiscountCodeByCode = async (token: string, code: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/code/${encodeURIComponent(code)}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Update discount code
export const updateDiscountCode = async (
	token: string,
	codeId: string,
	discount: UpdateDiscountForm
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/${codeId}`, {
		method: 'PUT',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(discount)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Delete discount code
export const deleteDiscountCode = async (token: string, codeId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/${codeId}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Validate discount code
export const validateDiscountCode = async (token: string, code: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/validate/${encodeURIComponent(code)}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Get users who used a specific discount code
export const getDiscountCodeUsers = async (token: string, code: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/users/${encodeURIComponent(code)}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin: Get user's discount usage history
export const getUserDiscountHistory = async (token: string, userId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/user/${userId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail ?? err.message ?? 'An error occurred';
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};
