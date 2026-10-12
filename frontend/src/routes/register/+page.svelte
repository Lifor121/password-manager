<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button } from '#lib/components/ui/button/index.js';
    import { Input } from '#lib/components/ui/input/index.js';
    import * as Card from '#lib/components/ui/card/index.js';
    import * as Label from '#lib/components/ui/label/index.js';
    import { authApi, ApiError } from '#lib/api';
    import {
        generateCryptoSalt,
        bufferToBase64,
        deriveAuthHash,
        deriveEncryptionKey,
        createEncryptedVaultKey
    } from '#lib/crypto/crypto';

    let email = $state('');
    let password = $state('');
    let confirmPassword = $state('');
    let loading = $state(false);
    let error = $state<string | null>(null);

    const MIN_MASTER_PASSWORD_LENGTH = 12;

    function validate(): string | null {
        const trimmed = email.trim();
        if (!trimmed || !trimmed.includes('@')) return 'Введите корректный email';
        if (password.length < MIN_MASTER_PASSWORD_LENGTH) {
            return `Мастер-пароль должен содержать минимум ${MIN_MASTER_PASSWORD_LENGTH} символов`;
        }
        if (password !== confirmPassword) return 'Пароли не совпадают';
        return null;
    }

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        error = null;

        const validationError = validate();
        if (validationError) { error = validationError; return; }

        loading = true;
        try {
            const normalizedEmail = email.trim().toLowerCase();

            // 1. Случайная соль — генерируем здесь и отправляем на сервер.
            const saltBytes = generateCryptoSalt();
            const cryptoSaltB64 = bufferToBase64(saltBytes);

            // 2. auth_hash → на сервер.
            const authHash = await deriveAuthHash(password, saltBytes);

            // 3. encryption_key → локально, шифрует vault_key.
            const encryptionKey = await deriveEncryptionKey(password, saltBytes);

            // 4. Случайный vault_key, зашифрованный encryption_key.
            const { encryptedVaultKey } = await createEncryptedVaultKey(encryptionKey);

            // 5. Регистрация.
            await authApi.register({
                email: normalizedEmail,
                master_password_hash: authHash,
                encrypted_vault_key: encryptedVaultKey,
                crypto_salt: cryptoSaltB64
            });

            password = '';
            confirmPassword = '';

            await goto('/login?registered=1');
        } catch (err) {
            if (err instanceof ApiError) {
                if (err.status === 409) error = 'Пользователь с таким email уже зарегистрирован';
                else if (err.status === 422) error = 'Некорректные данные. Проверьте поля';
                else if (err.status === 429) error = 'Слишком много попыток. Подождите минуту';
                else error = `Ошибка сервера (${err.status})`;
            } else {
                error = 'Не удалось создать аккаунт. Проверьте подключение';
                console.error('Registration failed:', err);
            }
        } finally {
            loading = false;
        }
    }
</script>

<div class="flex min-h-screen items-center justify-center p-4">
    <Card.Root class="w-full max-w-md">
        <Card.Header>
            <Card.Title>Создать аккаунт</Card.Title>
            <Card.Description>
                Мастер-пароль защищает ваше хранилище. Он не хранится на сервере —
                если вы его забудете, восстановить данные будет невозможно.
            </Card.Description>
        </Card.Header>

        <Card.Content>
            <form onsubmit={handleSubmit} class="flex flex-col gap-4">
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
                        autocomplete="new-password"
                        bind:value={password}
                        disabled={loading}
                        required
                    />
                    <p class="text-muted-foreground text-xs">
                        Минимум {MIN_MASTER_PASSWORD_LENGTH} символов. Используйте длинную
                        фразу — её легче запомнить и сложнее подобрать.
                    </p>
                </div>

                <div class="flex flex-col gap-2">
                    <Label.Root for="confirm">Повторите мастер-пароль</Label.Root>
                    <Input
                        id="confirm"
                        type="password"
                        autocomplete="new-password"
                        bind:value={confirmPassword}
                        disabled={loading}
                        required
                    />
                </div>

                {#if error}
                    <p class="text-destructive text-sm">{error}</p>
                {/if}

                <Button type="submit" disabled={loading} class="w-full">
                    {loading ? 'Создание аккаунта…' : 'Создать аккаунт'}
                </Button>
            </form>
        </Card.Content>

        <Card.Footer class="flex justify-center">
            <p class="text-muted-foreground text-sm">
                Уже есть аккаунт?
                <a href="/login" class="text-primary hover:underline">Войти</a>
            </p>
        </Card.Footer>
    </Card.Root>
</div>
