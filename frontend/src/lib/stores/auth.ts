import { writable, derived } from 'svelte/store';
import { resetVault } from './vault';

export const accessToken = writable<string | null>(null);
export const vaultKey = writable<CryptoKey | null>(null);
export const userEmail = writable<string | null>(null);
export const cryptoSalt = writable<string | null>(null);

export const isAuthenticated = derived(accessToken, ($t) => $t !== null);

export function setSession(params: {
    token: string;
    key: CryptoKey;
    email: string;
    salt: string;
}): void {
    accessToken.set(params.token);
    vaultKey.set(params.key);
    userEmail.set(params.email);
    cryptoSalt.set(params.salt);
}

export function clearSession(): void {
    accessToken.set(null);
    vaultKey.set(null);
    userEmail.set(null);
    cryptoSalt.set(null);
    resetVault();
}
