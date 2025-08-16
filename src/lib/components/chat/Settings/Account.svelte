<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user, config, settings } from '$lib/stores';
	import {
		updateUserProfile,
		createAPIKey,
		getAPIKey,
		getSessionUser
	} from '$lib/apis/auths';
	import { getTelegramOnboardingToken, checkTelegramConnected } from '$lib/apis/users';
	import { userCredits, fetchUserCredits } from '$lib/stores/credits';

	import UpdatePassword from './Account/UpdatePassword.svelte';
	import CreditProgressBar from '$lib/components/common/CreditProgressBar.svelte';
	import { getGravatarUrl } from '$lib/apis/utils';
	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';
	import { copyToClipboard } from '$lib/utils';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import dayjs from 'dayjs';

	const i18n = getContext('i18n');

	export let saveHandler: Function;
	export let saveSettings: Function;

	let profileImageUrl = '';
	let name = '';

	let webhookUrl = '';
	let showAPIKeys = false;

	let JWTTokenCopied = false;

	let APIKey = '';
	let APIKeyCopied = false;
	let profileImageInputElement: HTMLInputElement;

	let telegramConnected: boolean = false;
	let loading: boolean = true;

	const submitHandler = async () => {
		if (name !== $user?.name) {
			if (profileImageUrl === generateInitialsImage($user?.name) || profileImageUrl === '') {
				profileImageUrl = generateInitialsImage(name);
			}
		}

		if (webhookUrl !== $settings?.notifications?.webhook_url) {
			saveSettings({
				notifications: {
					...$settings.notifications,
					webhook_url: webhookUrl
				}
			});
		}

		const updatedUser = await updateUserProfile(localStorage.token, name, profileImageUrl).catch(
			(error) => {
				toast.error(`${error}`);
			}
		);

		if (updatedUser) {
			// Get Session User Info
			const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			await user.set(sessionUser);
			return true;
		}
		return false;
	};

	const createAPIKeyHandler = async () => {
		APIKey = await createAPIKey(localStorage.token);
		if (APIKey) {
			toast.success($i18n.t('API Key created.'));
		} else {
			toast.error($i18n.t('Failed to create API Key.'));
		}
	};

	onMount(async () => {
		name = $user?.name;
		profileImageUrl = $user?.profile_image_url;
		webhookUrl = $settings?.notifications?.webhook_url ?? '';

		APIKey = await getAPIKey(localStorage.token).catch((error) => {
			console.log(error);
			return '';
		});

		// Fetch user credits when visiting the account page
		await fetchUserCredits(localStorage.token);

		// Check Telegram connection status
		telegramConnected = await checkTelegramConnected(localStorage.token).catch((error) => {
			console.error('Failed to check Telegram connection status:', error);
			return false;
		});
		loading = false;
	});
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class=" overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<input
			id="profile-image-input"
			bind:this={profileImageInputElement}
			type="file"
			hidden
			accept="image/*"
			on:change={(e) => {
				const files = profileImageInputElement.files ?? [];
				let reader = new FileReader();
				reader.onload = (event) => {
					let originalImageUrl = `${event.target.result}`;

					const img = new Image();
					img.src = originalImageUrl;

					img.onload = function () {
						const canvas = document.createElement('canvas');
						const ctx = canvas.getContext('2d');

						// Calculate the aspect ratio of the image
						const aspectRatio = img.width / img.height;

						// Calculate the new width and height to fit within 250x250
						let newWidth, newHeight;
						if (aspectRatio > 1) {
							newWidth = 250 * aspectRatio;
							newHeight = 250;
						} else {
							newWidth = 250;
							newHeight = 250 / aspectRatio;
						}

						// Set the canvas size
						canvas.width = 250;
						canvas.height = 250;

						// Calculate the position to center the image
						const offsetX = (250 - newWidth) / 2;
						const offsetY = (250 - newHeight) / 2;

						// Draw the image on the canvas
						ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);

						// Get the base64 representation of the compressed image
						const compressedSrc = canvas.toDataURL('image/jpeg');

						// Display the compressed image
						profileImageUrl = compressedSrc;

						profileImageInputElement.files = null;
					};
				};

				if (
					files.length > 0 &&
					['image/gif', 'image/webp', 'image/jpeg', 'image/png'].includes(files[0]['type'])
				) {
					reader.readAsDataURL(files[0]);
				}
			}}
		/>

		<div class="space-y-1">
			<!-- <div class=" text-sm font-medium">{$i18n.t('Account')}</div> -->

			<div class="flex space-x-5">
				<div class="flex flex-col">
					<div class="self-center mt-2">
						<button
							class="relative rounded-full dark:bg-gray-700"
							type="button"
							on:click={() => {
								profileImageInputElement.click();
							}}
						>
							<img
								src={profileImageUrl !== '' ? profileImageUrl : generateInitialsImage(name)}
								alt="profile"
								class=" rounded-full size-16 object-cover"
							/>

							<div
								class="absolute flex justify-center rounded-full bottom-0 left-0 right-0 top-0 h-full w-full overflow-hidden bg-gray-700 bg-fixed opacity-0 transition duration-300 ease-in-out hover:opacity-50"
							>
								<div class="my-auto text-gray-100">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="w-5 h-5"
									>
										<path
											d="m2.695 14.762-1.262 3.155a.5.5 0 0 0 .65.65l3.155-1.262a4 4 0 0 0 1.343-.886L17.5 5.501a2.121 2.121 0 0 0-3-3L3.58 13.419a4 4 0 0 0-.885 1.343Z"
										/>
									</svg>
								</div>
							</div>
						</button>
					</div>
				</div>

				<div class="flex-1 flex flex-col self-center gap-0.5">
					<div class=" mb-0.5 text-sm font-medium">{$i18n.t('Profile Image')}</div>

					<div>
						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-full px-4 py-0.5 bg-gray-100 dark:bg-gray-850"
							on:click={async () => {
								if (canvasPixelTest()) {
									profileImageUrl = generateInitialsImage(name);
								} else {
									toast.info(
										$i18n.t(
											'Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.'
										),
										{
											duration: 1000 * 10
										}
									);
								}
							}}>{$i18n.t('Use Initials')}</button
						>

						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-full px-4 py-0.5 bg-gray-100 dark:bg-gray-850"
							on:click={async () => {
								const url = await getGravatarUrl(localStorage.token, $user?.email);

								profileImageUrl = url;
							}}>{$i18n.t('Use Gravatar')}</button
						>

						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-lg px-2 py-1"
							on:click={async () => {
								profileImageUrl = '/user.png';
							}}>{$i18n.t('Remove')}</button
						>
					</div>
				</div>
			</div>

			<div class="pt-0.5">
				<div class="flex flex-col w-full">
					<div class=" mb-1 font-medium">{$i18n.t('Name')}</div>

					<div class="flex-1">
						<input
							class="w-full dark:text-gray-300 bg-transparent outline-hidden"
							type="text"
							bind:value={name}
							required
							placeholder={$i18n.t('Enter your name')}
						/>
					</div>
				</div>
			</div>
			<hr class="border-gray-50 dark:border-gray-850 my-2" />

			{#if $userCredits?.plan_id !== undefined && $userCredits?.monthly_quota !== undefined}
				<section class="space-y-2">
					<div class="mb-1 font-medium">{$i18n.t('Plan Status')}</div>

					<!-- Plan + Status -->
					<div class="flex items-center gap-2">
						<!-- Plan Chip (flips to "Expired" when past period_end) -->
						{#if $userCredits?.current_period_end && dayjs($userCredits.current_period_end * 1000).isBefore(dayjs())}
							<!-- EXPIRED -->
							<span
								class="inline-flex items-center gap-1.5 px-2.5 py-0.5 font-semibold rounded-md
											 bg-red-100 text-red-700 ring-1 ring-inset ring-red-200
											 dark:bg-red-900/30 dark:text-red-200 dark:ring-red-800/60"
								aria-label={$i18n.t('Plan expired')}
							>
								<!-- tiny warning icon (inline SVG, no deps) -->
								<svg viewBox="0 0 20 20" class="w-3.5 h-3.5" fill="currentColor" aria-hidden="true">
									<path fill-rule="evenodd"
												d="M8.257 3.099c.765-1.36 2.72-1.36 3.485 0l6.518 11.59c.73 1.297-.198 2.911-1.742 2.911H3.48c-1.544 0-2.472-1.614-1.742-2.911L8.257 3.1zM11 14a1 1 0 10-2 0 1 1 0 002 0zm-.25-6.75a.75.75 0 00-1.5 0v4a.75.75 0 001.5 0v-4z"
												clip-rule="evenodd" />
								</svg>
								{$i18n.t('Expired')}
							</span>
						{:else}
							<!-- ACTIVE -->
							<span
								class="inline-flex items-center px-2.5 py-0.5 font-medium rounded-md
											 bg-[#21706d]/10 text-[#21706d]
											 dark:bg-[#21706d]/20 dark:text-[#21706d]/90 capitalize"
								aria-label={$i18n.t('Current Plan')}
							>
								{$userCredits?.plan_id}
							</span>
						{/if}

					</div>

					<!-- Dates + CTAs -->
					{#if $userCredits?.current_period_end}
						{#if dayjs($userCredits.current_period_end * 1000).isBefore(dayjs())}
							<!-- EXPIRED STATE -->
							<div class="mt-1 space-y-3">
								<p class="text-sm">
									{$i18n.t('Your plan expired on {{date}}. Reactivate now to restore access.', {
										date: dayjs($userCredits.current_period_end * 1000).format('LL')
									})}
								</p>
								<div class="flex items-center gap-2">
									<a
										href="/pricing"
										class="px-3.5 py-1.5 text-sm font-medium bg-[#21706d] hover:bg-[#21706d]/90 text-white transition rounded-lg"
										aria-label={$i18n.t('Reactivate Plan')}
									>
										{$i18n.t('Reactivate Plan')}
									</a>
								</div>
							</div>
						{:else}
							<!-- ACTIVE STATE -->
							{#key $userCredits.current_period_end}
								{#await Promise.resolve(dayjs($userCredits.current_period_end * 1000).diff(dayjs(), 'day')) then daysLeft}
									<div class="mt-1 space-y-2">
										<p class="text-sm">
											{$i18n.t('Your plan expires on {{date}} ({{days}} days left).', {
												date: dayjs($userCredits.current_period_end * 1000).format('LL'),
												days: daysLeft
											})}
										</p>
										<div class="flex items-center gap-2">
											<a
												href="/pricing"
												class="px-3.5 py-1.5 text-sm font-medium rounded-lg border border-[#21706d] text-[#21706d] hover:bg-[#21706d]/10 dark:hover:bg-[#21706d]/20 transition"
											>
												{$i18n.t('Change Plan')}
											</a>
										</div>
									</div>
								{/await}
							{/key}
						{/if}
					{/if}
				</section>
			{/if}

			<!--			 Credit Progress Bar -->
			<!--			{#if $userCredits?.credit_balance !== undefined && $userCredits?.monthly_quota !== undefined}-->
			<!--				<div class="py-2">-->
			<!--					<div class="flex flex-col w-full gap-2">-->
			<!--						<div class="mb-1 text-xs font-medium">{$i18n.t('Quota')}</div>-->
			<!--						<CreditProgressBar-->
			<!--							showDetails={false}-->
			<!--							currentCredits={$userCredits.credit_balance}-->
			<!--							totalCredits={$userCredits.monthly_quota}-->
			<!--							size="sm"-->
			<!--						/>-->
			<!--					</div>-->
			<!--				</div>-->
			<!--			{/if}-->
			<hr class="border-gray-50 dark:border-gray-850 mt-2" />


			{#if $config?.features?.enable_user_webhooks}
				<div class="pt-2">
					<div class="flex flex-col w-full">
						<div class=" mb-1 text-xs font-medium">{$i18n.t('Notification Webhook')}</div>

						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								type="url"
								placeholder={$i18n.t('Enter your webhook URL')}
								bind:value={webhookUrl}
								required
							/>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<hr class="border-gray-50 dark:border-gray-850 my-2" />

		<div class="my-2">
			<div class=" text-sm font-medium mb-2">{$i18n.t('Telegram')}</div>
			<div class="flex flex-col gap-2">
				<div class="flex justify-between items-center">
					<div class="text-xs text-gray-500">
						{$i18n.t('Connect your Telegram account to receive notifications.')}
					</div>
				</div>
				<div class="flex">

					<button
						class="flex gap-1.5 items-center font-medium px-3.5 py-1.5 rounded-lg bg-gray-100/70 disabled:cursor-not-allowed hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-850 transition"
						disabled={telegramConnected || loading}
						on:click={async () => {
							loading = true;
								const token = await getTelegramOnboardingToken(localStorage.token);
								if (token) {
									const url = `https://t.me/LabyAIBot?start=${token.token}`;
									await copyToClipboard(url);
									window.open(url, "_blank");

									toast.success('Onboarding link copied to clipboard. Paste it to your Telegram bot.');
									loading = false
								} else {
									toast.error('Failed to generate onboarding link.');
								}
							}}
					>
						{#if telegramConnected}
							{$i18n.t('Connected')}
						{:else if loading}
							{$i18n.t('Loading...')}
							<Spinner></Spinner>
						{:else}
							<Plus strokeWidth="2" className=" size-3.5" />
							{$i18n.t('Connect Telegram')}
						{/if}

					</button>

				</div>
			</div>
		</div>

		<hr class="border-gray-50 dark:border-gray-850 my-2" />

		{#if ($config?.features?.enable_api_key ?? true) || $user?.role === 'admin'}
			<div class="flex justify-between items-center text-sm mb-2">
				<div class="  font-medium">{$i18n.t('API keys')}</div>
				<button
					class=" text-xs font-medium text-gray-500"
					type="button"
					on:click={() => {
						showAPIKeys = !showAPIKeys;
					}}>{showAPIKeys ? $i18n.t('Hide') : $i18n.t('Show')}</button
				>
			</div>

			{#if showAPIKeys}
				<div class="flex flex-col gap-4">
					{#if $user?.role === 'admin'}
						<div class="justify-between w-full">
							<div class="flex justify-between w-full">
								<div class="self-center text-xs font-medium mb-1">{$i18n.t('JWT Token')}</div>
							</div>

							<div class="flex">
								<SensitiveInput value={localStorage.token} readOnly={true} />

								<button
									class="ml-1.5 px-1.5 py-1 dark:hover:bg-gray-850 transition rounded-lg"
									on:click={() => {
										copyToClipboard(localStorage.token);
										JWTTokenCopied = true;
										setTimeout(() => {
											JWTTokenCopied = false;
										}, 2000);
									}}
								>
									{#if JWTTokenCopied}
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 20 20"
											fill="currentColor"
											class="w-4 h-4"
										>
											<path
												fill-rule="evenodd"
												d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
												clip-rule="evenodd"
											/>
										</svg>
									{:else}
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 16 16"
											fill="currentColor"
											class="w-4 h-4"
										>
											<path
												fill-rule="evenodd"
												d="M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2ZM10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4h3Z"
												clip-rule="evenodd"
											/>
											<path
												fill-rule="evenodd"
												d="M3 6a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H3Zm1.75 2.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 0 0 0-1.5h-3.5ZM4 11.75a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z"
												clip-rule="evenodd"
											/>
										</svg>
									{/if}
								</button>
							</div>
						</div>
					{/if}

					{#if $config?.features?.enable_api_key ?? true}
						<div class="justify-between w-full">
							{#if $user?.role === 'admin'}
								<div class="flex justify-between w-full">
									<div class="self-center text-xs font-medium mb-1">{$i18n.t('API Key')}</div>
								</div>
							{/if}
							<div class="flex">
								{#if APIKey}
									<SensitiveInput value={APIKey} readOnly={true} />

									<button
										class="ml-1.5 px-1.5 py-1 dark:hover:bg-gray-850 transition rounded-lg"
										on:click={() => {
											copyToClipboard(APIKey);
											APIKeyCopied = true;
											setTimeout(() => {
												APIKeyCopied = false;
											}, 2000);
										}}
									>
										{#if APIKeyCopied}
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-4 h-4"
											>
												<path
													fill-rule="evenodd"
													d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
													clip-rule="evenodd"
												/>
											</svg>
										{:else}
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 16 16"
												fill="currentColor"
												class="w-4 h-4"
											>
												<path
													fill-rule="evenodd"
													d="M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2ZM10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4h3Z"
													clip-rule="evenodd"
												/>
												<path
													fill-rule="evenodd"
													d="M3 6a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H3Zm1.75 2.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 0 0 0-1.5h-3.5ZM4 11.75a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z"
													clip-rule="evenodd"
												/>
											</svg>
										{/if}
									</button>

									<Tooltip content={$i18n.t('Create new key')}>
										<button
											class=" px-1.5 py-1 dark:hover:bg-gray-850transition rounded-lg"
											on:click={() => {
												createAPIKeyHandler();
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												fill="none"
												viewBox="0 0 24 24"
												stroke-width="2"
												stroke="currentColor"
												class="size-4"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
												/>
											</svg>
										</button>
									</Tooltip>
								{:else}
									<button
										class="flex gap-1.5 items-center font-medium px-3.5 py-1.5 rounded-lg bg-gray-100/70 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-850 transition"
										on:click={() => {
											createAPIKeyHandler();
										}}
									>
										<Plus strokeWidth="2" className=" size-3.5" />

										{$i18n.t('Create new secret key')}</button
									>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			{/if}
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			on:click={async () => {
				const res = await submitHandler();

				if (res) {
					saveHandler();
				}
			}}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
