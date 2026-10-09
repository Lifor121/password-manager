<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import {
        filteredVaultItems,
        vaultLoading,
        vaultError,
        vaultSearchQuery,
        loadVault
    } from '$lib/stores/vault';

    onMount(() => {
        loadVault();
    });
</script>

<div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-semibold">Хранилище</h1>
        <Button onclick={() => goto('/vault/new')}>Создать запись</Button>
    </div>

    <Input
        bind:value={$vaultSearchQuery}
        placeholder="Поиск по названию, логину, URL или комментарию…"
    />

    {#if $vaultLoading}
        <p class="text-muted-foreground">Загрузка…</p>
    {:else if $vaultError}
        <p class="text-destructive">{$vaultError}</p>
    {:else if $filteredVaultItems.length === 0}
        <Card.Root>
            <Card.Content class="py-12 text-center">
                <p class="text-muted-foreground">
                    {$vaultSearchQuery
                        ? 'По вашему запросу ничего не найдено'
                        : 'В хранилище пока нет записей'}
                </p>
            </Card.Content>
        </Card.Root>
    {:else}
        <div class="flex flex-col gap-2">
            {#each $filteredVaultItems as item (item.id)}
                <button
                    type="button"
                    class="hover:bg-accent focus-visible:ring-ring rounded-lg border p-4 text-left transition focus-visible:ring-2 focus-visible:outline-none"
                    onclick={() => goto(`/vault/${item.id}`)}
                >
                    <div class="font-medium">{item.data.title}</div>
                    {#if item.data.login || item.data.url}
                        <div class="text-muted-foreground mt-1 flex gap-3 text-sm">
                            {#if item.data.login}
                                <span>{item.data.login}</span>
                            {/if}
                            {#if item.data.url}
                                <span class="truncate">{item.data.url}</span>
                            {/if}
                        </div>
                    {/if}
                </button>
            {/each}
        </div>
    {/if}
</div>
