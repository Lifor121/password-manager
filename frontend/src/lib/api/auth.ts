import { api } from './client';
import type {
    LoginRequest,
    LoginResponse,
    RegisterRequest
} from './types';

export const authApi = {
    register: (data: RegisterRequest) =>
        api.post<void>('/auth/register', data),

    login: (data: LoginRequest) =>
        api.post<LoginResponse>('/auth/login', data),

    logout: () => api.post<void>('/auth/logout', {})
};
