import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface DiscountCode {
	id?: string;
	code: string;
	discount_percent: number;
	expires_at?: number | null;
	usage_limit?: number | null;
	used_count: number;
	active: boolean;
	created_at?: number;
	updated_at?: number;
}

export interface CreateDiscountForm {
	code: string;
	discount_percent: number;
	expires_at?: number | null;
	usage_limit?: number | null;
	active?: boolean;
}

export interface UpdateDiscountForm {
	code?: string;
	discount_percent?: number;
	expires_at?: number | null;
	usage_limit?: number | null;
	active?: boolean;
}

export interface DiscountUsage {
	id: string;
	user_id: string;
	discount_code_id: string;
	used_at: number;
	user_name?: string;
	user_email?: string;
}

// Helper function to convert date string to Unix timestamp
const dateStringToTimestamp = (dateString: string | null): number | null => {
	if (!dateString) return null;
	return Math.floor(new Date(dateString + 'T23:59:59').getTime() / 1000);
};

// Helper function to convert Unix timestamp to date string
const timestampToDateString = (timestamp: number | null): string | null => {
	if (!timestamp) return null;
	return new Date(timestamp * 1000).toISOString().split('T')[0];
};

// Helper function to transform backend response to frontend format
const transformDiscountCode = (
	discount: DiscountCode
): DiscountCode & { expiry_date?: string | null } => {
	return {
		...discount,
		expiry_date: timestampToDateString(discount.expires_at ?? null)
	};
};

// Admin: Create a new discount code
export const createDiscountCode = async (
	token: string,
	discount: CreateDiscountForm & { expiry_date?: string | null }
) => {
	let error = null;

	// Convert expiry_date to expires_at if provided
	const submitData: CreateDiscountForm = {
		...discount,
		expires_at: discount.expiry_date ? dateStringToTimestamp(discount.expiry_date) : null
	};

	// Remove expiry_date from the payload since backend expects expires_at
	delete (submitData as CreateDiscountForm & { expiry_date?: string }).expiry_date;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(submitData)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((discount) => transformDiscountCode(discount))
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
		.then((discounts: DiscountCode[]) => discounts.map(transformDiscountCode))
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
		.then((discount) => transformDiscountCode(discount))
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
		.then((discount) => transformDiscountCode(discount))
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
	discount: UpdateDiscountForm & { expiry_date?: string | null }
) => {
	let error = null;

	// Convert expiry_date to expires_at if provided
	const submitData: UpdateDiscountForm = {
		...discount,
		expires_at: discount.expiry_date ? dateStringToTimestamp(discount.expiry_date) : null
	};

	// Remove expiry_date from the payload since backend expects expires_at
	delete (submitData as UpdateDiscountForm & { expiry_date?: string }).expiry_date;

	const res = await fetch(`${WEBUI_API_BASE_URL}/discount/${codeId}`, {
		method: 'PUT',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(submitData)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((discount) => transformDiscountCode(discount))
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
