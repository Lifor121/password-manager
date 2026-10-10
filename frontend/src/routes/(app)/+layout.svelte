<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button } from '#lib/components/ui/button/index.js';
    import { authApi } from '#lib/api';
    import { isAuthenticated, userEmail, clearSession } from '#lib/stores/auth';

    $effect(() => {
        if (!$isAuthenticated) {
            goto('/login');
        }
    });

    async function handleLogout() {
        try {
            await authApi.logout();
        } catch (err) {
            // Логаут не должен падать из-за сети — сессию всё равно очищаем
            console.error('Logout request failed:', err);
        } finally {
            clearSession();
            await goto('/login');
        }
    }
</script>

{#if $isAuthenticated}
    <div class="flex min-h-screen flex-col">
        <header class="border-b">
            <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
                <a href="/vault" class="text-lg font-semibold">
                    Password Manager
                </a>
                <div class="flex items-center gap-3">
                    <span class="text-muted-foreground hidden text-sm sm:inline">
                        {$userEmail}
                    </span>
                    <a
                        href="/settings"
                        class="text-muted-foreground hover:text-foreground text-sm"
                    >
                        Настройки
                    </a>
                    <Button variant="outline" size="sm" onclick={handleLogout}>
                        Выйти
                    </Button>
                </div>
            </div>
        </header>

        <main class="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
            <slot />
        </main>
    </div>
{/if}
