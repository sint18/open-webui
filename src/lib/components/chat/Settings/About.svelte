<script lang="ts">
	import { getContext } from 'svelte';
	import { WEBUI_BUILD_HASH, WEBUI_VERSION } from '$lib/constants';
	import { WEBUI_NAME } from '$lib/stores';

	const i18n = getContext('i18n');
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm mb-6">
	<div class="space-y-6 overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
				{$i18n.t('Laby AI')}
			</h1>
			<p class="text-lg text-gray-700 dark:text-gray-300 mb-6">
				{$i18n.t('Empowering Burmese creators with AI writing & coding tools')}
			</p>
			<p class="text-gray-600 dark:text-gray-400 leading-relaxed">
				{$i18n.t(
					'Laby AI is a premium subscription platform that delivers state‑of‑the‑art language models in a clean, localised workspace—so freelancers, agencies, and businesses in Myanmar can craft content and code faster than ever.'
				)}
			</p>
		</div>

		<div>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
				{$i18n.t('Why choose Laby AI')}
			</h2>
			<div class="space-y-3">
				<div>
					<strong class="text-gray-900 dark:text-gray-100">{$i18n.t('Ready in seconds')}</strong>
					<span class="text-gray-600 dark:text-gray-400">
						– {$i18n.t('Access advanced AI copy‑ and code‑generation without GPUs or setup.')}</span
					>
				</div>
				<div>
					<strong class="text-gray-900 dark:text-gray-100">{$i18n.t('Privacy & security')}</strong>
					<span class="text-gray-600 dark:text-gray-400">
						– {$i18n.t('We never train on or resell your data.')}</span
					>
				</div>
				<div>
					<strong class="text-gray-900 dark:text-gray-100">{$i18n.t('Myanmar‑first')}</strong>
					<span class="text-gray-600 dark:text-gray-400">
						– {$i18n.t(
							'Full Burmese interface, KBZPay & WavePay billing, and local support 7 days a week.'
						)}</span
					>
				</div>
				<div>
					<strong class="text-gray-900 dark:text-gray-100">{$i18n.t('Always improving')}</strong>
					<span class="text-gray-600 dark:text-gray-400">
						– {$i18n.t('New model upgrades roll out automatically for paying members.')}</span
					>
				</div>
			</div>
		</div>

		<div>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
				{$i18n.t('Our promise')}
			</h2>
			<p class="text-gray-600 dark:text-gray-400 leading-relaxed">
				{$i18n.t(
					'Your subscription funds continuous R&D and keeps our infrastructure fast, reliable, and secure—so you can focus on ideas, not tooling.'
				)}
			</p>
		</div>

		<div>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
				{$i18n.t('Meet the team')}
			</h2>
			<p class="text-gray-600 dark:text-gray-400 leading-relaxed">
				{$i18n.t(
					'Managed by the AI Code Lab Admin Team, our Myanmar‑based engineers, designers, and educators believe every creator deserves world‑class tools.'
				)}
			</p>
		</div>

		<div>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
				{$i18n.t('Credits')}
			</h2>
			<p class="text-gray-600 dark:text-gray-400">
				{$i18n.t('Emoji graphics by Twemoji, licensed under CC‑BY 4.0.')}
			</p>
		</div>

		<div class="pt-4">
			<p class="text-xs text-gray-500 dark:text-gray-500">
				{$i18n.t('Last updated: 30 June 2025')}
			</p>
		</div>
	</div>

	<!-- Version Information Section -->
	<div class="space-y-2">
		<div>
			<div class="text-xs text-gray-500">{$WEBUI_NAME}</div>
			<div class="text-xs text-gray-300 font-medium">{$i18n.t('Version')}: {WEBUI_VERSION}</div>
		</div>
	</div>
</div>
