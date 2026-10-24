<script lang="ts">
	import { page } from '$app/state';
	import LockIcon from '@lucide/svelte/icons/lock';
	import { Button } from '#lib/components/ui/button/index.js';

	interface ErrorInfo {
		title: string;
		description: string;
	}

	const knownErrors: Record<number, ErrorInfo> = {
		400: {
			title: 'Неверный запрос',
			description: 'Сервер не смог обработать запрос. Проверьте данные и попробуйте ещё раз.'
		},
		401: {
			title: 'Требуется вход',
			description: 'Сессия истекла или вы ещё не вошли в аккаунт. Войдите, чтобы продолжить.'
		},
		403: {
			title: 'Доступ запрещён',
			description: 'У вас нет прав для просмотра этой страницы. Обратитесь к владельцу аккаунта.'
		},
		404: {
			title: 'Страница не найдена',
			description: 'Возможно, ссылка устарела или страница была удалена. Проверьте адрес.'
		},
		429: {
			title: 'Слишком много запросов',
			description: 'Слишком много запросов подряд. Подождите немного и попробуйте снова.'
		},
		500: {
			title: 'Ошибка сервера',
			description: 'Что-то пошло не так на нашей стороне. Попробуйте обновить страницу позже.'
		},
		502: {
			title: 'Сервис недоступен',
			description: 'Сервер временно не отвечает. Попробуйте обновить страницу через пару минут.'
		},
		503: {
			title: 'Сервис недоступен',
			description: 'Сервис перегружен или находится на обслуживании. Попробуйте позже.'
		},
		504: {
			title: 'Сервер не отвечает',
			description: 'Превышено время ожидания ответа. Попробуйте обновить страницу ещё раз.'
		}
	};

	const fallback: ErrorInfo = {
		title: 'Что-то пошло не так',
		description: 'Произошла непредвиденная ошибка. Попробуйте вернуться на главную.'
	};

	const info = $derived(knownErrors[page.status] ?? fallback);
	const isServerError = $derived(page.status >= 500);

	function reloadPage() {
		window.location.reload();
	}
</script>

<svelte:head>
	<title>{page.status} — {info.title}</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<div class="flex min-h-screen flex-col">
	<header class="border-b">
		<div class="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-6 py-4">
			<a href="/" class="flex items-center gap-2 font-semibold">
				<span
					class="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground"
				>
					<LockIcon class="size-4" />
				</span>
				Password Manager
			</a>

			<Button variant="ghost" size="sm" href="/">На главную</Button>
		</div>
	</header>

	<main class="flex flex-1 items-center justify-center px-6 py-16">
		<div class="w-full max-w-lg text-center">
			<p class="text-7xl font-semibold tracking-tight text-muted-foreground/30">{page.status}</p>

			<h1 class="mt-4 text-2xl font-semibold tracking-tight sm:text-3xl">{info.title}</h1>
			<p class="mt-3 text-muted-foreground">{info.description}</p>

			<div class="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
				{#if page.status === 401}
					<Button size="lg" href="/login">Войти</Button>
					<Button size="lg" variant="outline" href="/">На главную</Button>
				{:else if isServerError}
					<Button size="lg" onclick={reloadPage}>Обновить страницу</Button>
					<Button size="lg" variant="outline" href="/">На главную</Button>
				{:else}
					<Button size="lg" href="/">На главную</Button>
					<Button size="lg" variant="outline" href="/login">Войти</Button>
				{/if}
			</div>
		</div>
	</main>
</div>
