<script lang="ts">
	import KeyRoundIcon from '@lucide/svelte/icons/key-round';
	import LockIcon from '@lucide/svelte/icons/lock';
	import ShieldCheckIcon from '@lucide/svelte/icons/shield-check';
	import SlidersHorizontalIcon from '@lucide/svelte/icons/sliders-horizontal';
	import { Button } from '#lib/components/ui/button/index.js';
</script>

<svelte:head>
	<title>Password Manager — zero-knowledge хранилище паролей</title>
	<meta
		name="description"
		content="Zero-knowledge менеджер паролей: записи шифруются в браузере, а мастер-пароль не покидает ваше устройство."
	/>
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

			<nav class="flex items-center gap-2">
				<Button variant="ghost" size="sm" href="/login">Войти</Button>
				<Button class="hidden sm:inline-flex" size="sm" href="/register">Создать аккаунт</Button>
			</nav>
		</div>
	</header>

	<main class="flex-1">
		<section class="mx-auto w-full max-w-5xl px-6 pt-20 pb-16 text-center">
			<span
				class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground"
			>
				<span class="size-1.5 rounded-full bg-green-500"></span>
				Zero-knowledge: сервер не видит ваши пароли
			</span>

			<h1 class="mx-auto mt-6 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
				Пароли, которые известны только вам
			</h1>

			<p class="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
				Password Manager хранит логины, пароли и заметки в зашифрованном виде. Ключ
				расшифровки выводится из мастер-пароля прямо в браузере и никогда не отправляется на
				сервер.
			</p>

			<div class="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
				<Button size="lg" class="w-full sm:w-auto" href="/register">Создать аккаунт</Button>
				<Button size="lg" variant="outline" class="w-full sm:w-auto" href="/login">Войти</Button>
			</div>

			<p class="mt-4 text-sm text-muted-foreground">
				Мастер-пароль не хранится на сервере — открыть хранилище можете только вы.
			</p>
		</section>

		<section class="border-y bg-muted/40">
			<div class="mx-auto w-full max-w-5xl px-6 py-16">
				<h2 class="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
					Безопасность по умолчанию
				</h2>
				<p class="mx-auto mt-3 max-w-xl text-center text-muted-foreground">
					Архитектура построена так, чтобы у сервера не было доступа к вашим данным.
				</p>

				<div class="mt-10 grid gap-4 sm:grid-cols-3">
					<div class="rounded-xl border bg-card p-6 shadow-xs">
						<div
							class="flex size-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground"
						>
							<ShieldCheckIcon class="size-5" />
						</div>
						<h3 class="mt-4 font-medium">Шифрование на клиенте</h3>
						<p class="mt-2 text-sm text-muted-foreground">
							Каждая запись шифруется в браузере алгоритмом AES-256-GCM. На сервер попадают
							только зашифрованные данные.
						</p>
					</div>

					<div class="rounded-xl border bg-card p-6 shadow-xs">
						<div
							class="flex size-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground"
						>
							<KeyRoundIcon class="size-5" />
						</div>
						<h3 class="mt-4 font-medium">Мастер-пароль остаётся у вас</h3>
						<p class="mt-2 text-sm text-muted-foreground">
							Сервер получает только производный хеш для входа (PBKDF2, 600 000 итераций).
							Ключ хранилища он расшифровать не может.
						</p>
					</div>

					<div class="rounded-xl border bg-card p-6 shadow-xs">
						<div
							class="flex size-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground"
						>
							<SlidersHorizontalIcon class="size-5" />
						</div>
						<h3 class="mt-4 font-medium">Всё под контролем</h3>
						<p class="mt-2 text-sm text-muted-foreground">
							Меняйте мастер-пароль без перешифровки записей, отзывайте сессии и удаляйте
							аккаунт вместе со всеми данными.
						</p>
					</div>
				</div>
			</div>
		</section>

		<section class="mx-auto w-full max-w-5xl px-6 py-16">
			<h2 class="text-center text-2xl font-semibold tracking-tight sm:text-3xl">
				Как это работает
			</h2>

			<ol class="mt-10 grid gap-8 sm:grid-cols-3">
				<li class="flex flex-col gap-3">
					<span
						class="flex size-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground"
					>
						1
					</span>
					<div>
						<h3 class="font-medium">Создайте аккаунт</h3>
						<p class="mt-1 text-sm text-muted-foreground">
							При регистрации генерируется случайный ключ хранилища и шифруется ключом из
							вашего мастер-пароля.
						</p>
					</div>
				</li>

				<li class="flex flex-col gap-3">
					<span
						class="flex size-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground"
					>
						2
					</span>
					<div>
						<h3 class="font-medium">Сохраните записи</h3>
						<p class="mt-1 text-sm text-muted-foreground">
							Название, логин, пароль, URL и комментарий шифруются в браузере до отправки на
							сервер.
						</p>
					</div>
				</li>

				<li class="flex flex-col gap-3">
					<span
						class="flex size-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground"
					>
						3
					</span>
					<div>
						<h3 class="font-medium">Войдите, когда нужно</h3>
						<p class="mt-1 text-sm text-muted-foreground">
							Ключ расшифровки собирается заново только после ввода мастер-пароля и остаётся
							в браузере.
						</p>
					</div>
				</li>
			</ol>
		</section>

		<section class="mx-auto w-full max-w-5xl px-6 pb-16">
			<div class="rounded-2xl border bg-card px-6 py-12 text-center shadow-xs">
				<h2 class="text-2xl font-semibold tracking-tight sm:text-3xl">
					Начните прямо сейчас
				</h2>
				<p class="mx-auto mt-3 max-w-xl text-muted-foreground">
					Для старта достаточно почты и надёжного мастер-пароля — минимум 12 символов.
				</p>

				<div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
					<Button size="lg" class="w-full sm:w-auto" href="/register">Создать аккаунт</Button>
					<p class="text-sm text-muted-foreground">
						Уже есть аккаунт?
						<a href="/login" class="text-primary hover:underline">Войти</a>
					</p>
				</div>
			</div>
		</section>
	</main>

	<footer class="border-t">
		<div
			class="mx-auto flex w-full max-w-5xl flex-col gap-1 px-6 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between"
		>
			<p>Password Manager</p>
			<p>AES-256-GCM · PBKDF2 · zero-knowledge</p>
		</div>
	</footer>
</div>
