// ---------- Auth ----------

export interface RegisterRequest {
    email: string;
    master_password_hash: string;
    encrypted_vault_key: string;
    crypto_salt: string;
}

export interface AuthParamsResponse {
    crypto_salt: string;
}

export interface LoginRequest {
    email: string;
    master_password_hash: string;
}

export interface LoginResponse {
    access_token: string;
    encrypted_vault_key: string;
    crypto_salt: string;
}

export interface ChangePasswordRequest {
    old_password_hash: string;
    new_password_hash: string;
    new_encrypted_vault_key: string;
}

// ---------- Vault ----------

export interface VaultItemDto {
    id: string; // UUID
    encrypted_title: string;
    title_blind_index?: string | null;
    encrypted_login?: string | null;
    encrypted_password: string;
    encrypted_url?: string | null;
    encrypted_comment?: string | null;
    created_at: string;
    updated_at: string;
}

export interface VaultItemListResponse {
    items: VaultItemDto[];
    total: number;
}

export interface VaultItemCreatePayload {
    encrypted_title: string;
    encrypted_password: string;
    encrypted_login?: string | null;
    encrypted_url?: string | null;
    encrypted_comment?: string | null;
    title_blind_index?: string | null;
}
