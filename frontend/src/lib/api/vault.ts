import { api } from './client';
import type {
    VaultItemDto,
    VaultItemMutationResponse,
    VaultItemPayload
} from './types';

export const vaultApi = {
    list: () => api.get<VaultItemDto[]>('/vault/items'),

    get: (id: number) => api.get<VaultItemDto>(`/vault/items/${id}`),

    create: (data: VaultItemPayload) =>
        api.post<VaultItemMutationResponse>('/vault/items', data),

    update: (id: number, data: VaultItemPayload) =>
        api.put<VaultItemMutationResponse>(`/vault/items/${id}`, data),

    remove: (id: number) => api.del<void>(`/vault/items/${id}`)
};
