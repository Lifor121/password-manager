<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { get } from 'svelte/store';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Label from '#lib/components/ui/label/index.js';
	import { vaultApi, ApiError } from '#lib/api';
	import { encryptVaultItem } from '#lib/crypto/crypto';
	import { vaultKey } from '#lib/stores/auth';
	import { loadVault } from '#lib/stores/vault';

	let title = $state('');
	let login = $state('');
	let password = $state('');
	let url = $state('');
	let comment = $state('');
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit(event: SubmitEvent) {
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

		const key = get(vaultKey);
		if (!key) {
			error = 'Хранилище заблокировано';
			return;
		}

		loading = true;
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

			await vaultApi.create({
				encrypted_title: fields.encrypted_title,
				encrypted_password: fields.encrypted_password,
				encrypted_login: fields.encrypted_login,
				encrypted_url: fields.encrypted_url,
				encrypted_comment: fields.encrypted_comment
			});

			await loadVault();
			await goto(resolve('/(app)/vault'));
		} catch (err) {
			console.error('Create vault item failed:', err);
			if (err instanceof ApiError) {
				if (err.status === 401) {
					error = 'Сессия истекла — войдите заново';
				} else if (err.status === 413) {
					error = 'Данные слишком большие';
				} else if (err.status === 422) {
					error = 'Некорректные данные записи';
				} else if (err.status === 429) {
					error = 'Слишком много запросов. Подождите минуту';
				} else {
					error = `Ошибка сервера (${err.status})`;
				}
			} else {
				error = 'Не удалось сохранить запись. Проверьте подключение';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-semibold">Новая запись</h1>
		<Button variant="outline" onclick={() => goto(resolve('/(app)/vault'))}>Отмена</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<Card.Title>Данные записи</Card.Title>
			<Card.Description>
				Все поля шифруются в браузере — сервер видит только шифртекст.
			</Card.Description>
		</Card.Header>

		<Card.Content>
			<form onsubmit={handleSubmit} class="flex flex-col gap-4">
				<div class="flex flex-col gap-2">
					<Label.Root for="title">Название</Label.Root>
					<Input
						id="title"
						bind:value={title}
						placeholder="Например, GitHub"
						disabled={loading}
						required
					/>
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="login">Логин</Label.Root>
					<Input id="login" bind:value={login} autocomplete="off" disabled={loading} />
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="password">Пароль</Label.Root>
					<Input
						id="password"
						type="text"
						bind:value={password}
						autocomplete="new-password"
						disabled={loading}
						required
					/>
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="url">URL</Label.Root>
					<Input id="url" bind:value={url} disabled={loading} />
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="comment">Комментарий</Label.Root>
					<Input id="comment" bind:value={comment} disabled={loading} />
				</div>

				{#if error}
					<p class="text-sm text-destructive">{error}</p>
				{/if}

				<Button type="submit" disabled={loading}>
					{loading ? 'Сохранение…' : 'Создать запись'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
</div>
