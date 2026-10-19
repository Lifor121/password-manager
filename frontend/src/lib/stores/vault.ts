// src/lib/stores/vault.ts
import { writable, derived, get } from 'svelte/store';
import { vaultApi } from '#lib/api';
import { decryptVaultItem, type VaultItemData } from '#lib/crypto/crypto';
import { vaultKey } from './auth';

export interface DecryptedVaultItem {
	id: string; // UUID с бэкенда
	data: VaultItemData;
	updated_at: string;
}

export const vaultItems = writable<DecryptedVaultItem[]>([]);
export const vaultLoading = writable(false);
export const vaultError = writable<string | null>(null);
export const vaultSearchQuery = writable('');

export const filteredVaultItems = derived([vaultItems, vaultSearchQuery], ([$items, $query]) => {
	const q = $query.trim().toLowerCase();
	if (!q) return $items;
	return $items.filter((item) =>
		[item.data.title, item.data.login, item.data.url, item.data.comment].some((value) =>
			(value ?? '').toLowerCase().includes(q)
		)
	);
});

export async function loadVault(): Promise<void> {
	const key = get(vaultKey);
	if (!key) {
		vaultError.set('Хранилище заблокировано');
		return;
	}

	vaultLoading.set(true);
	vaultError.set(null);
	try {
		// GET /vault/items отвечает объектом {items, total}, а не массивом.
		const response = await vaultApi.list();
		const decrypted = await Promise.all(
			response.items.map(async (dto) => ({
				id: dto.id,
				updated_at: dto.updated_at,
				data: await decryptVaultItem(dto, key)
			}))
		);
		vaultItems.set(decrypted);
	} catch (err) {
		console.error('Failed to load vault:', err);
		vaultError.set('Не удалось загрузить хранилище');
	} finally {
		vaultLoading.set(false);
	}
}

export function resetVault(): void {
	vaultItems.set([]);
	vaultSearchQuery.set('');
	vaultError.set(null);
}
