const PBKDF2_ITERATIONS = 600_000;
const PBKDF2_HASH = 'SHA-256';
const KEY_LENGTH = 256;
const SALT_LENGTH = 16;
const IV_LENGTH = 12;

const ENC_INFO = new TextEncoder().encode('pm:v1:enc');
const AUTH_INFO = new TextEncoder().encode('pm:v1:auth');

// ---------- base64 helpers ----------

export function bufferToBase64(buffer: ArrayBuffer | Uint8Array): string {
    const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

export function base64ToBuffer(base64: string): Uint8Array {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

// ---------- salt ----------

/** Случайная соль 16 байт — генерируется на регистрации, дальше сервер её хранит. */
export function generateCryptoSalt(): Uint8Array {
    return crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
}

/** Соль-домен: расширяем базовую соль инфо-строкой для разделения выводов. */
function withInfo(salt: Uint8Array, info: Uint8Array): Uint8Array {
    const combined = new Uint8Array(salt.length + info.length);
    combined.set(salt, 0);
    combined.set(info, salt.length);
    return combined;
}

// ---------- KDF ----------

async function importPassword(password: string): Promise<CryptoKey> {
    return crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(password),
        'PBKDF2',
        false,
        ['deriveKey', 'deriveBits']
    );
}

/**
 * Ключ шифрования — им шифруется/расшифровывается vault_key.
 * НИКОГДА не покидает браузер.
 */
export async function deriveEncryptionKey(
    masterPassword: string,
    cryptoSalt: Uint8Array
): Promise<CryptoKey> {
    const keyMaterial = await importPassword(masterPassword);
    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: withInfo(cryptoSalt, ENC_INFO),
            iterations: PBKDF2_ITERATIONS,
            hash: PBKDF2_HASH
        },
        keyMaterial,
        { name: 'AES-GCM', length: KEY_LENGTH },
        false,
        ['encrypt', 'decrypt']
    );
}

/**
 * Auth-хеш — строка, которая уходит на сервер для аутентификации.
 * Это НЕ ключ шифрования: компрометация сервера не даёт расшифровать vault_key.
 */
export async function deriveAuthHash(
    masterPassword: string,
    cryptoSalt: Uint8Array
): Promise<string> {
    const keyMaterial = await importPassword(masterPassword);
    const bits = await crypto.subtle.deriveBits(
        {
            name: 'PBKDF2',
            salt: withInfo(cryptoSalt, AUTH_INFO),
            iterations: PBKDF2_ITERATIONS,
            hash: PBKDF2_HASH
        },
        keyMaterial,
        KEY_LENGTH
    );
    return bufferToBase64(bits);
}

// ---------- AES-GCM примитивы ----------

export async function encryptString(plaintext: string, key: CryptoKey): Promise<string> {
    const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
    const ciphertext = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        new TextEncoder().encode(plaintext)
    );
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.length);
    return bufferToBase64(combined);
}

export async function decryptString(encrypted: string, key: CryptoKey): Promise<string> {
    const combined = base64ToBuffer(encrypted);
    const iv = combined.slice(0, IV_LENGTH);
    const ciphertext = combined.slice(IV_LENGTH);
    const plaintext = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
    );
    return new TextDecoder().decode(plaintext);
}

// ---------- Vault key: генерация / wrap / unwrap ----------

export async function generateVaultKey(): Promise<CryptoKey> {
    return crypto.subtle.generateKey(
        { name: 'AES-GCM', length: KEY_LENGTH },
        true,
        ['encrypt', 'decrypt']
    );
}

async function exportKeyRaw(key: CryptoKey): Promise<string> {
    return bufferToBase64(await crypto.subtle.exportKey('raw', key));
}

async function importKeyRaw(rawBase64: string): Promise<CryptoKey> {
    return crypto.subtle.importKey(
        'raw',
        base64ToBuffer(rawBase64),
        { name: 'AES-GCM', length: KEY_LENGTH },
        true,
        ['encrypt', 'decrypt']
    );
}

/** Регистрация: генерирует vault_key и возвращает его же в зашифрованном виде. */
export async function createEncryptedVaultKey(
    encryptionKey: CryptoKey
): Promise<{ vaultKey: CryptoKey; encryptedVaultKey: string }> {
    const vaultKey = await generateVaultKey();
    const rawVaultKey = await exportKeyRaw(vaultKey);
    const encryptedVaultKey = await encryptString(rawVaultKey, encryptionKey);
    return { vaultKey, encryptedVaultKey };
}

/** Логин: расшифровывает vault_key ключом шифрования. */
export async function unlockVaultKey(
    encryptedVaultKey: string,
    encryptionKey: CryptoKey
): Promise<CryptoKey> {
    const rawVaultKey = await decryptString(encryptedVaultKey, encryptionKey);
    return importKeyRaw(rawVaultKey);
}

/** Смена пароля: переупаковывает существующий vault_key новым ключом шифрования. */
export async function rewrapVaultKey(
    vaultKey: CryptoKey,
    newEncryptionKey: CryptoKey
): Promise<string> {
    const rawVaultKey = await exportKeyRaw(vaultKey);
    return encryptString(rawVaultKey, newEncryptionKey);
}

// ---------- Vault item: раздельные поля ----------

export interface VaultItemData {
    title: string;
    password: string;
    login?: string;
    url?: string;
    comment?: string;
}

export interface EncryptedVaultItemFields {
    encrypted_title: string;
    encrypted_password: string;
    encrypted_login: string | null;
    encrypted_url: string | null;
    encrypted_comment: string | null;
}

/**
 * Шифрует поля карточки ОТДЕЛЬНО, каждое — со своим nonce.
 * Пустые опциональные поля → null (не отправляем мусор).
 */
export async function encryptVaultItem(
    data: VaultItemData,
    vaultKey: CryptoKey
): Promise<EncryptedVaultItemFields> {
    const enc = (s?: string) =>
        s && s.length > 0 ? encryptString(s, vaultKey) : Promise.resolve(null);

    return {
        encrypted_title: await encryptString(data.title, vaultKey),
        encrypted_password: await encryptString(data.password, vaultKey),
        encrypted_login: await enc(data.login),
        encrypted_url: await enc(data.url),
        encrypted_comment: await enc(data.comment)
    };
}

export async function decryptVaultItem(
    dto: {
        encrypted_title: string;
        encrypted_password: string;
        encrypted_login?: string | null;
        encrypted_url?: string | null;
        encrypted_comment?: string | null;
    },
    vaultKey: CryptoKey
): Promise<VaultItemData> {
    const dec = (s?: string | null) =>
        s ? decryptString(s, vaultKey) : Promise.resolve(undefined);

    return {
        title: await decryptString(dto.encrypted_title, vaultKey),
        password: await decryptString(dto.encrypted_password, vaultKey),
        login: await dec(dto.encrypted_login),
        url: await dec(dto.encrypted_url),
        comment: await dec(dto.encrypted_comment)
    };
}
