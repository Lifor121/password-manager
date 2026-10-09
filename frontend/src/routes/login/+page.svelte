<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import { Button } from '$lib/components/ui/button/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import * as Label from '$lib/components/ui/label/index.js';
    import { authApi, ApiError } from '$lib/api';
    import {
        saltFromEmail,
        deriveMasterKey,
        deriveMasterPasswordHash,
        unlockVaultKey
    } from '$lib/crypto/crypto';
    import { setSession } from '$lib/stores/auth';

    let email = $state('');
    let password = $state('');
    let loading = $state(false);
    let error = $state<string | null>(null);

    // Показываем сообщение, если пришли с ?registered=1
    const justRegistered = $derived(page.url.searchParams.get('registered') === '1');

    // ... остальной код без изменений
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
