<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Label from '#lib/components/ui/label/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { vaultApi, ApiError } from '#lib/api';
	import { encryptVaultItem, decryptVaultItem } from '#lib/crypto/crypto';
	import { vaultKey } from '#lib/stores/auth';
	import { loadVault } from '#lib/stores/vault';

	const itemId = $derived(page.params.id ?? '');

	let title = $state('');
	let login = $state('');
	let password = $state('');
	let url = $state('');
	let comment = $state('');

	let loading = $state(true);
	let saving = $state(false);
	let showPassword = $state(false);
	let error = $state<string | null>(null);
	let confirmDelete = $state(false);

	function mapError(err: unknown): string {
		if (err instanceof ApiError) {
			if (err.status === 401) return 'Сессия истекла — войдите заново';
			if (err.status === 404) return 'Запись не найдена';
			if (err.status === 422) return 'Некорректные данные записи';
			if (err.status === 429) return 'Слишком много запросов. Подождите минуту';
			return `Ошибка сервера (${err.status})`;
		}
		return 'Не удалось выполнить операцию. Проверьте подключение';
	}

	onMount(async () => {
		const key = get(vaultKey);
		if (!key) {
			error = 'Хранилище заблокировано';
			loading = false;
			return;
		}
		if (!itemId) {
			error = 'Запись не найдена';
			loading = false;
			return;
		}
		try {
			const dto = await vaultApi.get(itemId);
			const data = await decryptVaultItem(dto, key);
			title = data.title;
			login = data.login ?? '';
			password = data.password;
			url = data.url ?? '';
			comment = data.comment ?? '';
		} catch (err) {
			console.error('Load vault item failed:', err);
			error = mapError(err);
		} finally {
			loading = false;
		}
	});

	async function handleSave(event: SubmitEvent) {
		event.preventDefault();
		error = null;

		if (!title.trim()) {
			error = 'Введите название записи';
			return;
		}
		if (!password) {
			error = 'Введите пароль';
			return;
		}
		if (!itemId) {
			error = 'Запись не найдена';
			return;
		}

		const key = get(vaultKey);
		if (!key) {
			error = 'Хранилище заблокировано';
			return;
		}

		saving = true;
		try {
			const fields = await encryptVaultItem(
				{
					title: title.trim(),
					login: login.trim() || undefined,
					password,
					url: url.trim() || undefined,
					comment: comment.trim() || undefined
				},
				key
			);

			await vaultApi.update(itemId, {
				encrypted_title: fields.encrypted_title,
				encrypted_password: fields.encrypted_password,
				encrypted_login: fields.encrypted_login,
				encrypted_url: fields.encrypted_url,
				encrypted_comment: fields.encrypted_comment
			});

			await loadVault();
			await goto(resolve('/(app)/vault'));
		} catch (err) {
			console.error('Update vault item failed:', err);
			error = mapError(err);
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		error = null;
		if (!itemId) {
			error = 'Запись не найдена';
			return;
		}
		saving = true;
		try {
			await vaultApi.remove(itemId);
			await loadVault();
			confirmDelete = false;
			await goto(resolve('/(app)/vault'));
		} catch (err) {
			console.error('Delete vault item failed:', err);
			error = mapError(err);
			confirmDelete = false;
		} finally {
			saving = false;
		}
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-semibold">Запись</h1>
		<Button variant="outline" onclick={() => goto(resolve('/(app)/vault'))}>К списку</Button>
	</div>

	{#if loading}
		<p class="text-muted-foreground">Загрузка…</p>
	{:else}
		<Card.Root>
			<Card.Content class="py-6">
				<form onsubmit={handleSave} class="flex flex-col gap-4">
					<div class="flex flex-col gap-2">
						<Label.Root for="title">Название</Label.Root>
						<Input id="title" bind:value={title} disabled={saving} required />
					</div>

					<div class="flex flex-col gap-2">
						<Label.Root for="login">Логин</Label.Root>
						<Input id="login" bind:value={login} disabled={saving} />
					</div>

					<div class="flex flex-col gap-2">
						<Label.Root for="password">Пароль</Label.Root>
						<div class="flex gap-2">
							<Input
								id="password"
								type={showPassword ? 'text' : 'password'}
								bind:value={password}
								autocomplete="new-password"
								disabled={saving}
								required
							/>
							<Button variant="outline" onclick={() => (showPassword = !showPassword)}>
								{showPassword ? 'Скрыть' : 'Показать'}
							</Button>
						</div>
					</div>

					<div class="flex flex-col gap-2">
						<Label.Root for="url">URL</Label.Root>
						<Input id="url" bind:value={url} disabled={saving} />
					</div>

					<div class="flex flex-col gap-2">
						<Label.Root for="comment">Комментарий</Label.Root>
						<Input id="comment" bind:value={comment} disabled={saving} />
					</div>

					{#if error}
						<p class="text-sm text-destructive">{error}</p>
					{/if}

					<div class="flex items-center justify-between gap-3">
						<Button
							type="button"
							variant="destructive"
							onclick={() => (confirmDelete = true)}
							disabled={saving}
						>
							Удалить
						</Button>
						<Button type="submit" disabled={saving}>
							{saving ? 'Сохранение…' : 'Сохранить'}
						</Button>
					</div>
				</form>
			</Card.Content>
		</Card.Root>
	{/if}
</div>

<Dialog.Root bind:open={confirmDelete}>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>Удалить запись?</Dialog.Title>
			<Dialog.Description>Запись будет удалена без возможности восстановления.</Dialog.Description>
		</Dialog.Header>
		<Dialog.Footer class="flex justify-end gap-2">
			<Button variant="outline" onclick={() => (confirmDelete = false)}>Отмена</Button>
			<Button variant="destructive" onclick={handleDelete} disabled={saving}>
				{saving ? 'Удаление…' : 'Удалить'}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
