import { writable, derived } from 'svelte/store';

export const accessToken = writable<string | null>(null);
export const vaultKey = writable<CryptoKey | null>(null);
export const userEmail = writable<string | null>(null);

export const isAuthenticated = derived(
    accessToken,
    ($token) => $token !== null
);

export function setSession(
    token: string,
    key: CryptoKey,
    email: string
): void {
    accessToken.set(token);
    vaultKey.set(key);
    userEmail.set(email);
}

export function clearSession(): void {
    accessToken.set(null);
    vaultKey.set(null);
    userEmail.set(null);
    // TODO: очистить кэш записей хранилища
}
