// src/lib/crypto/crypto.ts

const PBKDF2_ITERATIONS = 600_000;
const PBKDF2_HASH = 'SHA-256';
const KEY_LENGTH = 256;
const SALT_LENGTH = 16;
const IV_LENGTH = 12;

// ---------- Утилиты для base64 <-> Uint8Array ----------

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

// ---------- Генерация соли / ключей ----------

export function generateSalt(): Uint8Array {
    return crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
}

/**
 * Генерирует случайный ключ хранилища (Vault Key).
 * Экспортируется как "raw" для дальнейшего шифрования мастер-ключом.
 */
export async function generateVaultKey(): Promise<CryptoKey> {
    return crypto.subtle.generateKey(
        { name: 'AES-GCM', length: KEY_LENGTH },
        true, // extractable — нужно, чтобы зашифровать его мастер-ключом
        ['encrypt', 'decrypt']
    );
}

// ---------- Деривация мастер-ключа из мастер-пароля ----------

/**
 * Превращает мастер-пароль в CryptoKey через PBKDF2.
 * Этот ключ НИКОГДА не покидает браузер.
 */
export async function deriveMasterKey(
    masterPassword: string,
    salt: Uint8Array
): Promise<CryptoKey> {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        enc.encode(masterPassword),
        { name: 'PBKDF2' },
        false,
        ['deriveKey']
    );

    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt,
            iterations: PBKDF2_ITERATIONS,
            hash: PBKDF2_HASH
        },
        keyMaterial,
        { name: 'AES-GCM', length: KEY_LENGTH },
        false, // мастер-ключ не экспортируем
        ['encrypt', 'decrypt']
    );
}

/**
 * Хэш мастер-пароля для отправки на сервер (аутентификация).
 * Это НЕ мастер-ключ — другой derivation, чтобы компромисс одного
 * не раскрывал другой.
 */
export async function deriveMasterPasswordHash(
    masterPassword: string,
    salt: Uint8Array
): Promise<string> {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        enc.encode(masterPassword),
        { name: 'PBKDF2' },
        false,
        ['deriveBits']
    );

    const bits = await crypto.subtle.deriveBits(
        {
            name: 'PBKDF2',
            salt,
            iterations: PBKDF2_ITERATIONS,
            hash: PBKDF2_HASH
        },
        keyMaterial,
        KEY_LENGTH
    );

    return bufferToBase64(bits);
}

// ---------- Шифрование / дешифрование ----------

/**
 * Шифрует строку данным ключом (AES-GCM).
 * Возвращает строку вида base64(iv || ciphertext).
 */
export async function encryptString(
    plaintext: string,
    key: CryptoKey
): Promise<string> {
    const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));
    const enc = new TextEncoder();
    const ciphertext = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        enc.encode(plaintext)
    );

    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.length);
    return bufferToBase64(combined);
}

/**
 * Расшифровывает строку, полученную из encryptString.
 */
export async function decryptString(
    encrypted: string,
    key: CryptoKey
): Promise<string> {
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

// ---------- Специализированные операции ----------

/**
 * Экспортирует Vault Key в base64 (raw), чтобы затем зашифровать его мастер-ключом.
 */
async function exportKeyRaw(key: CryptoKey): Promise<string> {
    const raw = await crypto.subtle.exportKey('raw', key);
    return bufferToBase64(raw);
}

/**
 * Импортирует Vault Key из base64 (raw).
 */
async function importKeyRaw(rawBase64: string): Promise<CryptoKey> {
    const raw = base64ToBuffer(rawBase64);
    return crypto.subtle.importKey(
        'raw',
        raw,
        { name: 'AES-GCM', length: KEY_LENGTH },
        true,
        ['encrypt', 'decrypt']
    );
}

/**
 * Регистрация:
 * 1. Генерируем Vault Key.
 * 2. Шифруем его мастер-ключом.
 * 3. Возвращаем зашифрованный vaultKey (base64) для отправки на сервер.
 *    Сам Vault Key тоже возвращаем — он понадобится для работы в текущей сессии.
 */
export async function createEncryptedVaultKey(
    masterKey: CryptoKey
): Promise<{ vaultKey: CryptoKey; encryptedVaultKey: string }> {
    const vaultKey = await generateVaultKey();
    const rawVaultKey = await exportKeyRaw(vaultKey);
    const encryptedVaultKey = await encryptString(rawVaultKey, masterKey);
    return { vaultKey, encryptedVaultKey };
}

/**
 * Логин:
 * Расшифровываем Vault Key мастер-ключом.
 */
export async function unlockVaultKey(
    encryptedVaultKey: string,
    masterKey: CryptoKey
): Promise<CryptoKey> {
    const rawVaultKey = await decryptString(encryptedVaultKey, masterKey);
    return importKeyRaw(rawVaultKey);
}

// ---------- Работа с записями хранилища ----------

export interface VaultItemData {
    title: string;
    login: string;
    password: string;
    url?: string;
    comment?: string;
}

/**
 * Шифрует JSON-объект записи в одну строку для отправки на сервер.
 */
export async function encryptVaultItem(
    data: VaultItemData,
    vaultKey: CryptoKey
): Promise<string> {
    return encryptString(JSON.stringify(data), vaultKey);
}

/**
 * Расшифровывает строку от сервера в объект записи.
 */
export async function decryptVaultItem(
    encryptedData: string,
    vaultKey: CryptoKey
): Promise<VaultItemData> {
    const json = await decryptString(encryptedData, vaultKey);
    return JSON.parse(json) as VaultItemData;
}

export function saltFromEmail(email: string): Uint8Array {
    const normalized = email.trim().toLowerCase();
    return new TextEncoder().encode(normalized);
}
