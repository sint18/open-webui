import type { LayoutLoad } from './$types';
import { getSessionUser } from '$lib/apis/auths';

export const load: LayoutLoad = async () => {
        const sessionUser = await getSessionUser(localStorage.token).catch(() => null);
        return {
                user: sessionUser,
                roles: sessionUser ? [sessionUser.role] : []
        };
};
