import { api } from './client';
import type { ChangePasswordRequest } from './types';

export const usersApi = {
    changePassword: (data: ChangePasswordRequest) =>
        api.put<void>('/users/me/password', data),

    deleteAccount: () => api.del<void>('/users/me')
};
