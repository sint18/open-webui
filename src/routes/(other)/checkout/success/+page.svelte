<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { checkTelegramConnected, getTelegramOnboardingToken } from '$lib/apis/users';
	import { copyToClipboard } from '$lib/utils';
	import CheckmarkCircle from '$lib/components/icons/CircleCheck.svelte';

	let telegramConnected = false;
	const i18n = getContext('i18n');

	const handleEnableNotifications = async () => {
		try {
			const tokenResponse = await getTelegramOnboardingToken(localStorage.token);
			if (tokenResponse && tokenResponse.token) {
				const url = `https://t.me/LabyAIBot?start=${tokenResponse.token}`;
				await copyToClipboard(url);
				toast.success('Onboarding link copied to clipboard. Paste it to your Telegram bot.');
				window.open(url, '_blank');
			} else {
				toast.error('Failed to generate onboarding link.');
			}
		} catch (error) {
			toast.error('An error occurred while generating the onboarding link.');
		}
	};

	onMount(async () => {
		telegramConnected = await checkTelegramConnected(localStorage.token).catch((error) => {
			console.error('Failed to check Telegram connection status:', error);
			return false;
		});
	});
</script>

<div class="flex flex-col items-center justify-center h-full text-center px-4">
	{#if telegramConnected}
		<div class="max-w-md w-full">
			<div class="mb-6">
				<CheckmarkCircle className="w-24 h-24 text-teal-500 mx-auto" />
			</div>
			<h1 class="text-3xl font-bold text-gray-800 dark:text-white mb-4">
				{$i18n.t("You're all set!")}
			</h1>
			<p class="text-gray-600 dark:text-gray-400 mb-8">
				{$i18n.t("✨ Thank you for uploading your payment screenshot. We'll notify you on Telegram as soon as your payment is confirmed.")}
			</p>
			<p class="text-gray-600 dark:text-gray-400 mb-8">
				{$i18n.t("No need to do anything — we've already linked your Telegram for instant updates.")}
			</p>

			<div class="space-y-4">
				<span
					class="inline-block w-fit px-3 py-1 text-sm font-medium rounded-xl bg-[#21706d]/10 text-[#21706d] dark:bg-[#21706d]/20 dark:text-teal-500 capitalize"
				>
					{$i18n.t("📲 Telegram: Connected")}
				</span>
			</div>
		</div>
	{:else}
		<div class="max-w-md w-full">
			<div class="mb-6">
				<CheckmarkCircle className="w-24 h-24 text-teal-500 mx-auto" />
			</div>
			<h1 class="text-3xl font-bold text-gray-800 dark:text-white mb-4">
				{$i18n.t("📲 Final Step: Confirm via Telegram")}
			</h1>
			<p class="text-gray-600 dark:text-gray-400 mb-8">
				{$i18n.t("To complete your payment submission and receive confirmation, you must connect with our Telegram bot.")}
			</p>
			<p class="text-gray-600 dark:text-gray-400 mb-8">
				{$i18n.t("🔐 This keeps your notifications secure and instant.")}
			</p>

			<div class="space-y-4">
				<button
					on:click={handleEnableNotifications}
					class="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:text-gray-200 text-white rounded-xl px-4 py-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
				>
					<span>{$i18n.t("🔗 Connect with Telegram")}</span>
				</button>
			</div>
		</div>
	{/if}
</div>
