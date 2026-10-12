<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import { Button } from '#lib/components/ui/button/index.js';
    import { Input } from '#lib/components/ui/input/index.js';
    import * as Card from '#lib/components/ui/card/index.js';
    import * as Label from '#lib/components/ui/label/index.js';
    import { authApi, ApiError } from '#lib/api';
    import {
        base64ToBuffer,
        deriveAuthHash,
        deriveEncryptionKey,
        unlockVaultKey
    } from '#lib/crypto/crypto';
    import { setSession } from '#lib/stores/auth';

    let email = $state('');
    let password = $state('');
    let loading = $state(false);
    let error = $state<string | null>(null);

    const justRegistered = $derived(page.url.searchParams.get('registered') === '1');

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        error = null;

        const trimmedEmail = email.trim().toLowerCase();
        if (!trimmedEmail || !password) {
            error = 'Введите email и мастер-пароль';
            return;
        }

        loading = true;
        try {
            // 1. Соль с сервера.
            const { crypto_salt } = await authApi.getParams(trimmedEmail);
            const saltBytes = base64ToBuffer(crypto_salt);

            // 2. auth_hash → на сервер.
            const authHash = await deriveAuthHash(password, saltBytes);

            // 3. Логин.
            const response = await authApi.login({
                email: trimmedEmail,
                master_password_hash: authHash
            });

            // 4. Локальная разблокировка vault_key.
            const encryptionKey = await deriveEncryptionKey(password, saltBytes);
            let vaultKey: CryptoKey;
            try {
                vaultKey = await unlockVaultKey(response.encrypted_vault_key, encryptionKey);
            } catch (unlockErr) {
                console.error('Vault unlock failed:', unlockErr);
                error = 'Не удалось разблокировать хранилище. Проверьте мастер-пароль';
                return;
            }

            // 5. Сессия. Соль берём из ответа логина (сервер мог обновить).
            setSession({
                token: response.access_token,
                key: vaultKey,
                email: trimmedEmail,
                salt: response.crypto_salt ?? crypto_salt
            });

            password = '';
            await goto('/vault');
        } catch (err) {
            if (err instanceof ApiError) {
                if (err.status === 401 || err.status === 404) {
                    error = 'Неверный email или мастер-пароль';
                } else if (err.status === 429) {
                    error = 'Слишком много попыток. Подождите минуту';
                } else {
                    error = `Ошибка сервера (${err.status})`;
                }
            } else {
                error = 'Не удалось войти. Проверьте подключение';
                console.error('Login failed:', err);
            }
        } finally {
            loading = false;
        }
    }
</script>

<div class="flex min-h-screen items-center justify-center p-4">
    <Card.Root class="w-full max-w-md">
        <Card.Header>
            <Card.Title>Вход</Card.Title>
            <Card.Description>
                Введите мастер-пароль, чтобы разблокировать хранилище.
            </Card.Description>
        </Card.Header>

        <Card.Content>
            <form onsubmit={handleSubmit} class="flex flex-col gap-4">
                {#if justRegistered}
                    <p class="text-sm text-green-600 dark:text-green-400">
                        Аккаунт создан. Войдите, чтобы продолжить.
                    </p>
                {/if}

                <div class="flex flex-col gap-2">
                    <Label.Root for="email">Email</Label.Root>
                    <Input
                        id="email"
                        type="email"
                        autocomplete="email"
                        bind:value={email}
                        disabled={loading}
                        required
                    />
                </div>

                <div class="flex flex-col gap-2">
                    <Label.Root for="password">Мастер-пароль</Label.Root>
                    <Input
                        id="password"
                        type="password"
                        autocomplete="current-password"
                        bind:value={password}
                        disabled={loading}
                        required
                    />
                </div>

                {#if error}
                    <p class="text-destructive text-sm">{error}</p>
                {/if}

                <Button type="submit" disabled={loading} class="w-full">
                    {loading ? 'Разблокировка…' : 'Войти'}
                </Button>
            </form>
        </Card.Content>

        <Card.Footer class="flex justify-center">
            <p class="text-muted-foreground text-sm">
                Нет аккаунта?
                <a href="/register" class="text-primary hover:underline">
                    Зарегистрироваться
                </a>
            </p>
        </Card.Footer>
    </Card.Root>
</div>
