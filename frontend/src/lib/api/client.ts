import { get } from 'svelte/store';
import { accessToken, clearSession } from '$lib/stores/auth';

const API_BASE_URL = '/api';

export class ApiError extends Error {
    constructor(
        public status: number,
        public body: unknown,
        message?: string
    ) {
        super(message ?? `HTTP ${status}`);
        this.name = 'ApiError';
    }
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = get(accessToken);
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Токен истёк или отозван — сбрасываем сессию.
        clearSession();
        throw new ApiError(401, null, 'Unauthorized');
    }

    if (!response.ok) {
        let body: unknown = null;
        try {
            body = await response.json();
        } catch {
            // тело может быть пустым или не-JSON
        }
        throw new ApiError(response.status, body);
    }

    if (response.status === 204) {
        return undefined as T;
    }

    return (await response.json()) as T;
}

export const api = {
    get: <T>(url: string) => request<T>(url, { method: 'GET' }),
    post: <T>(url: string, data: unknown) =>
        request<T>(url, { method: 'POST', body: JSON.stringify(data) }),
    put: <T>(url: string, data: unknown) =>
        request<T>(url, { method: 'PUT', body: JSON.stringify(data) }),
    del: <T = void>(url: string) => request<T>(url, { method: 'DELETE' })
};
