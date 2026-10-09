// ---------- Auth ----------

export interface RegisterRequest {
    email: string;
    master_password_hash: string;
    encrypted_vault_key: string;
}

export interface LoginRequest {
    email: string;
    master_password_hash: string;
}

export interface LoginResponse {
    access_token: string;
    encrypted_vault_key: string;
}

// ---------- Users ----------

export interface ChangePasswordRequest {
    old_password_hash: string;
    new_password_hash: string;
    new_encrypted_vault_key: string;
}

// ---------- Vault ----------

/** То, что возвращает сервер по одной записи. */
export interface VaultItemDto {
    id: number;
    encrypted_data: string;
    updated_at: string;
}

/** Ответ при создании/обновлении. */
export interface VaultItemMutationResponse {
    id: number;
    updated_at: string;
}

/** Body для создания/обновления. */
export interface VaultItemPayload {
    encrypted_data: string;
}
