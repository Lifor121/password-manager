// src/lib/stores/auth.ts
import { writable } from 'svelte/store';

export const accessToken = writable<string | null>(null);
export const vaultKey = writable<CryptoKey | null>(null);

export function clearSession() {
    accessToken.set(null);
    vaultKey.set(null);
    // TODO: очистить другие сторы (vault items), localStorage и т.п.
}
