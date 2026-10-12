import { api } from './client';
import type {
    AuthParamsResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest
} from './types';

export const authApi = {
    register: (data: RegisterRequest) =>
        api.post<void>('/auth/register', data),

    getParams: (email: string) =>
        api.get<AuthParamsResponse>(
            `/auth/params?email=${encodeURIComponent(email)}`
        ),

    login: (data: LoginRequest) =>
        api.post<LoginResponse>('/auth/login', data),

    logout: () => api.post<void>('/auth/logout', {})
};
