export const jsonHeaders = (token: string) => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
});

export const handle = async (res: Response) => {
    if (!res.ok) {
        throw await res.json();
    }
    return res.json();
};

