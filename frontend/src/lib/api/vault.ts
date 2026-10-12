import { api } from './client';
import type {
    VaultItemCreatePayload,
    VaultItemDto,
    VaultItemListResponse
} from './types';

export const vaultApi = {
    list: () => api.get<VaultItemListResponse>('/vault/items'),
    get: (id: string) => api.get<VaultItemDto>(`/vault/items/${id}`),
    create: (data: VaultItemCreatePayload) =>
        api.post<VaultItemDto>('/vault/items', data),
    update: (id: string, data: VaultItemCreatePayload) =>
        api.put<VaultItemDto>(`/vault/items/${id}`, data),
    remove: (id: string) => api.del<void>(`/vault/items/${id}`)
};
