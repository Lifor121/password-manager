<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button } from '$lib/components/ui/button/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import * as Label from '$lib/components/ui/label/index.js';
    import { authApi, ApiError } from '$lib/api';
    import {
        saltFromEmail,
        deriveMasterKey,
        deriveMasterPasswordHash,
        createEncryptedVaultKey
    } from '$lib/crypto/crypto';

    let email = $state('');
    let password = $state('');
    let confirmPassword = $state('');
    let loading = $state(false);
    let error = $state<string | null>(null);

    const MIN_MASTER_PASSWORD_LENGTH = 12;

    function validate(): string | null {
        const trimmed = email.trim();
        if (!trimmed || !trimmed.includes('@')) {
            return 'Введите корректный email';
        }
        if (password.length < MIN_MASTER_PASSWORD_LENGTH) {
            return `Мастер-пароль должен содержать минимум ${MIN_MASTER_PASSWORD_LENGTH} символов`;
        }
        if (password !== confirmPassword) {
            return 'Пароли не совпадают';
        }
        return null;
    }

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        error = null;

        const validationError = validate();
        if (validationError) {
            error = validationError;
            return;
        }

        loading = true;
        try {
            const normalizedEmail = email.trim().toLowerCase();
            const salt = saltFromEmail(normalizedEmail);

            // 1. Выводим мастер-ключ (никогда не покидает браузер)
            const masterKey = await deriveMasterKey(password, salt);

            // 2. Выводим хэш для аутентификации на сервере
            const masterPasswordHash = await deriveMasterPasswordHash(password, salt);

            // 3. Генерируем Vault Key и шифруем его мастер-ключом
            const { encryptedVaultKey } = await createEncryptedVaultKey(masterKey);

            // 4. Регистрируемся
            await authApi.register({
                email: normalizedEmail,
                master_password_hash: masterPasswordHash,
                encrypted_vault_key: encryptedVaultKey
            });

            // Стираем чувствительные данные из реактивного состояния
            password = '';
            confirmPassword = '';

            await goto('/login?registered=1');
        } catch (err) {
            if (err instanceof ApiError) {
                if (err.status === 409) {
                    error = 'Пользователь с таким email уже зарегистрирован';
                } else if (err.status === 400) {
                    error = 'Некорректные данные. Проверьте email и попробуйте снова';
                } else {
                    error = `Ошибка сервера (${err.status}). Попробуйте позже`;
                }
            } else {
                error = 'Не удалось создать аккаунт. Попробуйте ещё раз';
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
