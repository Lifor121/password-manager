<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { get } from 'svelte/store';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Label from '#lib/components/ui/label/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { usersApi, ApiError } from '#lib/api';
	import {
		base64ToBuffer,
		deriveAuthHash,
		deriveEncryptionKey,
		rewrapVaultKey
	} from '#lib/crypto/crypto';
	import { vaultKey, cryptoSalt, userEmail, clearSession } from '#lib/stores/auth';

	const MIN_MASTER_PASSWORD_LENGTH = 12;

	let currentPassword = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let changing = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	let confirmDelete = $state(false);
	let deleting = $state(false);
	let deleteError = $state<string | null>(null);

	async function handleChangePassword(event: SubmitEvent) {
		event.preventDefault();
		error = null;
		success = null;

		const saltB64 = get(cryptoSalt);
		const key = get(vaultKey);
		if (!saltB64 || !key) {
			error = 'Сессия истекла — войдите заново';
			return;
		}
		if (!currentPassword || !newPassword) {
			error = 'Заполните все поля';
			return;
		}
		if (newPassword.length < MIN_MASTER_PASSWORD_LENGTH) {
			error = `Новый мастер-пароль должен содержать минимум ${MIN_MASTER_PASSWORD_LENGTH} символов`;
			return;
		}
		if (newPassword !== confirmPassword) {
			error = 'Новые пароли не совпадают';
			return;
		}

		changing = true;
		try {
			const saltBytes = base64ToBuffer(saltB64);

			// Хеши и переупаковка ключа считаются локально — пароль на сервер не уходит.
			const oldHash = await deriveAuthHash(currentPassword, saltBytes);
			const newHash = await deriveAuthHash(newPassword, saltBytes);
			const newEncryptionKey = await deriveEncryptionKey(newPassword, saltBytes);
			const rewrappedKey = await rewrapVaultKey(key, newEncryptionKey);

			await usersApi.changePassword({
				old_password_hash: oldHash,
				new_password_hash: newHash,
				new_encrypted_vault_key: rewrappedKey
			});

			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
			success = 'Мастер-пароль обновлён. Сессии на других устройствах отозваны.';
		} catch (err) {
			console.error('Change password failed:', err);
			if (err instanceof ApiError) {
				if (err.status === 400) error = 'Текущий мастер-пароль неверен';
				else if (err.status === 401) error = 'Сессия истекла — войдите заново';
				else if (err.status === 422) error = 'Некорректные данные';
				else if (err.status === 429) error = 'Слишком много запросов. Подождите минуту';
				else error = `Ошибка сервера (${err.status})`;
			} else {
				error = 'Не удалось сменить пароль. Проверьте подключение';
			}
		} finally {
			changing = false;
		}
	}

	async function handleDeleteAccount() {
		deleteError = null;
		deleting = true;
		try {
			await usersApi.deleteAccount();
			confirmDelete = false;
			// Сначала редирект, потом очистка: иначе $effect layout успевает
			// перехватить пустую сессию и увести на /login раньше нас.
			await goto(resolve('/login'));
			clearSession();
		} catch (err) {
			console.error('Delete account failed:', err);
			if (err instanceof ApiError && err.status === 401) {
				deleteError = 'Сессия истекла — войдите заново';
			} else {
				deleteError = 'Не удалось удалить аккаунт. Проверьте подключение';
			}
		} finally {
			deleting = false;
		}
	}
</script>

<div class="flex flex-col gap-6">
	<h1 class="text-2xl font-semibold">Настройки</h1>

	<Card.Root>
		<Card.Header>
			<Card.Title>Аккаунт</Card.Title>
			<Card.Description>Электронная почта для входа</Card.Description>
		</Card.Header>
		<Card.Content>
			<p class="text-sm">{$userEmail}</p>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Смена мастер-пароля</Card.Title>
			<Card.Description>
				Записи остаются зашифрованными тем же ключом — переупаковка происходит локально в браузере.
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<form onsubmit={handleChangePassword} class="flex flex-col gap-4">
				<div class="flex flex-col gap-2">
					<Label.Root for="current">Текущий мастер-пароль</Label.Root>
					<Input
						id="current"
						type="password"
						autocomplete="current-password"
						bind:value={currentPassword}
						disabled={changing}
						required
					/>
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="new">Новый мастер-пароль</Label.Root>
					<Input
						id="new"
						type="password"
						autocomplete="new-password"
						bind:value={newPassword}
						disabled={changing}
						required
					/>
					<p class="text-xs text-muted-foreground">
						Минимум {MIN_MASTER_PASSWORD_LENGTH} символов.
					</p>
				</div>

				<div class="flex flex-col gap-2">
					<Label.Root for="confirm">Повторите новый пароль</Label.Root>
					<Input
						id="confirm"
						type="password"
						autocomplete="new-password"
						bind:value={confirmPassword}
						disabled={changing}
						required
					/>
				</div>

				{#if error}
					<p class="text-sm text-destructive">{error}</p>
				{/if}
				{#if success}
					<p class="text-sm text-green-600 dark:text-green-400">{success}</p>
				{/if}

				<Button type="submit" disabled={changing}>
					{changing ? 'Обновление…' : 'Сменить пароль'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title class="text-destructive">Удаление аккаунта</Card.Title>
			<Card.Description>Аккаунт, все записи и сессии будут удалены безвозвратно.</Card.Description>
		</Card.Header>
		<Card.Content>
			<Button variant="destructive" onclick={() => (confirmDelete = true)}>Удалить аккаунт</Button>
		</Card.Content>
	</Card.Root>
</div>

<Dialog.Root bind:open={confirmDelete}>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>Удалить аккаунт?</Dialog.Title>
			<Dialog.Description>
				Все записи хранилища и активные сессии будут удалены. Отменить это действие невозможно.
			</Dialog.Description>
		</Dialog.Header>

		{#if deleteError}
			<p class="text-sm text-destructive">{deleteError}</p>
		{/if}

		<Dialog.Footer class="flex justify-end gap-2">
			<Button variant="outline" onclick={() => (confirmDelete = false)}>Отмена</Button>
			<Button variant="destructive" onclick={handleDeleteAccount} disabled={deleting}>
				{deleting ? 'Удаление…' : 'Удалить навсегда'}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
