import { redirect } from '@sveltejs/kit';
import { get } from 'svelte/store';
import { isAuthenticated } from '#lib/stores/auth';

// Сессия хранится только в памяти браузера, поэтому страницу рендерим на клиенте.
export const ssr = false;

export function load() {
	// Авторизованным пользователям главная не нужна — сразу в хранилище.
	if (get(isAuthenticated)) {
		redirect(307, '/vault');
	}
}
