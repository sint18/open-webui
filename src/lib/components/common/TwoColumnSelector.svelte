<script lang="ts">
	import { DropdownMenu } from 'bits-ui';

	import Fuse from 'fuse.js';

	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';

	import ChatBubbleOval from '$lib/components/icons/ChatBubbleOval.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { toast } from 'svelte-sonner';

	import { getOllamaVersion } from '$lib/apis/ollama';

	import {
		models,
		mobile,
		settings,
		config,
		type Model,
		temporaryChatEnabled,
		user
	} from '$lib/stores';
	import { getModels } from '$lib/apis';
	import { trackEvent, ANALYTICS_EVENTS } from '$lib/utils/analytics';

	import dayjs from '$lib/dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import {
		getCompanyName,
		getLogoForModel,
		getModelSpeciality,
		getVendorIcon,
		formatModelName
	} from '$lib/utils/helper-functions';
	import { goto } from '$app/navigation';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';

	dayjs.extend(relativeTime);

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let id = '';
	export let value = '';
	export let placeholder = 'Select a model';
	export let searchEnabled = true;
	export let searchPlaceholder = $i18n.t('Search a model');

	export let showTemporaryChatControl = false;

	export let items: {
		label: string;
		value: string;
		model: Model;
		icon?: string;
		[key: string]: any;
	}[] = [];

	export let className = 'w-[40rem]';
	export let triggerClassName = 'text-lg';

	let show = false;
	let selectedModel = '';
	$: selectedModel = items.find((item) => item.value === value) ?? '';

	let searchValue = '';
	let selectedModelIdx = 0;
	let selectedVendorIdx = 0;
	let modelItemEls: HTMLElement[] = [];
	let hideLockedModels = false;
	let upgradeToastShown = false;
	let ollamaVersion = null;

	$: selectedVendor = vendors[selectedVendorIdx] || vendors[0];

	$: filteredModels = (() => {
		let baseModels = selectedVendor?.models || [];

		// Apply search filter first
		if (searchValue) {
			baseModels = fuse
				.search(searchValue)
				.map((e) => e.item)
				.filter((item) => baseModels.some((model) => model.value === item.value));
		}

		return baseModels;
	})();

	$: vendors = (() => {
		const vendorMap = new Map();

		// Filter items based on hideLockedModels setting
		const availableItems = hideLockedModels
			? items.filter((item) => $user?.role === 'admin' || item.model.can_use !== false)
			: items;

		// Add "All Models" vendor first
		vendorMap.set('All Models', {
			name: 'All Models',
			icon: '📋',
			models: availableItems,
			count: availableItems.length
		});

		// Get recent models and filter them if needed
		const allRecentModels = getRecentModels();
		const recentModels = hideLockedModels
			? allRecentModels.filter((item) => $user?.role === 'admin' || item.model.can_use !== false)
			: allRecentModels;

		// Add "Recent" vendor if there are recent models
		if (recentModels.length > 0) {
			vendorMap.set('★ Recent', {
				name: '★ Recent',
				icon: '★',
				models: recentModels,
				count: recentModels.length
			});
		}

		// Group remaining models by vendor
		availableItems.forEach((item) => {
			const vendor = getCompanyName(item.model);
			if (!vendorMap.has(vendor)) {
				vendorMap.set(vendor, {
					name: vendor,
					icon: getVendorIcon(vendor),
					models: [],
					count: 0
				});
			}
			vendorMap.get(vendor).models.push(item);
			vendorMap.get(vendor).count++;
		});

		// Sort models within each vendor
		vendorMap.forEach((vendor) => {
			vendor.models.sort((a: any, b: any) => a.label.localeCompare(b.label));
		});

		return Array.from(vendorMap.values());
	})();

	const fuse = new Fuse(items, {
		keys: ['value', 'label', 'model.name'],
		threshold: 0.4
	});

	function getRecentModels() {
		// Get recent models from localStorage or some other logic
		const recent = JSON.parse(localStorage.getItem('recentModels') || '[]');
		return items.filter((item) => recent.includes(item.value)).slice(0, 5);
	}

	async function scrollSelectedIntoView() {
		// wait for the DOM to update
		await tick();
		const el = modelItemEls[selectedModelIdx];
		if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	}

	/**
	 * Usage: <button use:collect={index}>…
	 * It will keep modelItemEls[index] = the DOM node.
	 */
	function collect(node: HTMLElement, index: number) {
		modelItemEls[index] = node;
		return {
			update(newIndex: number) {
				modelItemEls[newIndex] = node;
			},
			destroy() {
				modelItemEls[index] = undefined;
			}
		};
	}

	const showUpgradeToast = (item: any) => {
		if (upgradeToastShown) return;

		upgradeToastShown = true;

		// Track insufficient credits interaction
		trackEvent(ANALYTICS_EVENTS.PRICING_LINK_CLICKED, {
			source: 'model_locked_toast',
			current_page: window.location.pathname,
			model_attempted: item.value,
			model_name: item.label
		});

		toast($i18n.t('Unlock • Premium Models'), {
			description: $i18n.t(`Upgrade your plan to access {{model}}.`, { model: item.label }),
			action: {
				label: $i18n.t('Upgrade Now'),
				onClick: () => {
					// Track the actual click to pricing
					trackEvent(ANALYTICS_EVENTS.PRICING_LINK_CLICKED, {
						source: 'insufficient_credits_toast',
						current_page: window.location.pathname,
						model_attempted: item.value,
						model_name: item.label
					});
					goto(`/pricing?model=${item.value}`);
				}
			},
			duration: 5000,
			unstyled: true,
			classes: {
				toast:
					'bg-teal-100 text-teal-900 dark:bg-teal-800 dark:text-teal-50 rounded-xl shadow-xl ring-2 ring-teal-300 dark:ring-teal-600 p-4',
				title: 'font-semibold text-teal-900 dark:text-white text-sm mb-1',
				description: 'text-teal-800 dark:text-teal-200 text-xs',
				actionButton:
					'mt-4 inline-flex items-center rounded-full bg-teal-600 hover:bg-teal-700 px-3 py-1 text-sm font-semibold text-white transition duration-150 ease-in-out',
				closeButton:
					'absolute top-2 right-2 text-teal-700 hover:text-teal-900 dark:text-teal-300 dark:hover:text-white'
			},
			onDismiss: () => {
				upgradeToastShown = false;
			}
		});
	};

	// Reset the flag after the toast duration
	setTimeout(() => {
		upgradeToastShown = false;
	}, 5000);

	function selectModel(item: any) {
		if (item.model.can_use === false) {
			showUpgradeToast(item);
			return;
		}

		const previousModel = value;
		value = item.value;

		// Track model selection
		trackEvent(ANALYTICS_EVENTS.MODEL_SELECTOR_CLICKED, {
			user_id: $user?.id,
			selected_model: item.value,
			selected_model_name: item.label,
			previous_model: previousModel,
			context: 'model_selected',
			vendor: getCompanyName(item.model)
		});

		// Update recent models
		const recent = JSON.parse(localStorage.getItem('recentModels') || '[]');
		const updated = [item.value, ...recent.filter((v) => v !== item.value)].slice(0, 5);
		localStorage.setItem('recentModels', JSON.stringify(updated));

		show = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!show) return;

		switch (e.code) {
			case 'ArrowLeft':
				e.preventDefault();
				selectedVendorIdx = Math.max(0, selectedVendorIdx - 1);
				selectedModelIdx = 0;
				break;
			case 'ArrowRight':
				e.preventDefault();
				selectedVendorIdx = Math.min(vendors.length - 1, selectedVendorIdx + 1);
				selectedModelIdx = 0;
				break;
			case 'ArrowUp':
				e.preventDefault();
				selectedModelIdx = Math.max(0, selectedModelIdx - 1);
				scrollSelectedIntoView();
				break;
			case 'ArrowDown':
				e.preventDefault();
				selectedModelIdx = Math.min(filteredModels.length - 1, selectedModelIdx + 1);
				scrollSelectedIntoView();
				break;
			case 'Enter':
				e.preventDefault();
				if (filteredModels[selectedModelIdx]) {
					if (filteredModels[selectedModelIdx].model.can_use === false) {
						return;
					}
					selectModel(filteredModels[selectedModelIdx]);
				}
				break;
			case 'Escape':
				e.preventDefault();
				show = false;
				break;
		}
	}

	/* ───────────────── Swipe to change vendor ───────────────── */
	let touchStartX: number | null = null;
	const SWIPE_PX = 50; // adjust to taste

	function handleTouchStart(e: TouchEvent) {
		touchStartX = e.touches[0].clientX;
	}

	function handleTouchEnd(e: TouchEvent) {
		if (touchStartX === null) return;
		const dx = e.changedTouches[0].clientX - touchStartX;
		if (Math.abs(dx) > SWIPE_PX) {
			if (dx < 0 && selectedVendorIdx < vendors.length - 1) {
				selectedVendorIdx += 1;
			} else if (dx > 0 && selectedVendorIdx > 0) {
				selectedVendorIdx -= 1;
			}
			selectedModelIdx = null;
			scrollSelectedIntoView();
		}
		touchStartX = null;
	}

	onMount(async () => {
		ollamaVersion = await getOllamaVersion(localStorage.token).catch(() => false);
		document.addEventListener('keydown', handleKeydown);

		return () => {
			document.removeEventListener('keydown', handleKeydown);
		};
	});

	const resetView = async () => {
		await tick();
		selectedModelIdx = 0;
		selectedVendorIdx = 0;

		// Find the vendor that contains the selected model
		const modelVendorIdx = vendors.findIndex((vendor) =>
			vendor.models.some((model) => model.value === value)
		);
		if (modelVendorIdx >= 0) {
			selectedVendorIdx = modelVendorIdx;
			const modelIdx = vendors[modelVendorIdx].models.findIndex((model) => model.value === value);
			if (modelIdx >= 0) {
				selectedModelIdx = modelIdx;
			}
		}
	};
</script>

<DropdownMenu.Root
	bind:open={show}
	onOpenChange={async () => {
		searchValue = '';
		window.setTimeout(() => document.getElementById('model-search-input')?.focus(), 0);
		resetView();

		// Track model selector click when opened
		if (show) {
			trackEvent(ANALYTICS_EVENTS.MODEL_SELECTOR_CLICKED, {
				user_id: $user?.id,
				current_model: selectedModel?.valueOf || null,
				available_models_count: items.length,
				context: 'dropdown_open'
			});
		}
	}}
	closeFocus={false}
>
	<DropdownMenu.Trigger
		class="relative w-full font-primary"
		aria-label={placeholder}
		id="model-selector-{id}-button"
	>
		<button
			class="flex w-full text-left px-0.5 outline-hidden bg-transparent truncate {triggerClassName} justify-between font-medium placeholder-gray-400 focus:outline-hidden"
			on:mouseenter={async () => {
				models.set(
					await getModels(
						localStorage.token,
						$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
					)
				);
			}}
			type="button"
		>
			{#if selectedModel}
				{formatModelName(selectedModel?.label)}
			{:else}
				{placeholder}
			{/if}
			<ChevronDown className="self-center ml-2 size-3" strokeWidth="2.5" />
		</button>
	</DropdownMenu.Trigger>

	<DropdownMenu.Content
		class="z-40 w-full md:w-[40rem] max-w-[calc(100vw-1rem)]
         justify-start rounded-xl bg-white dark:bg-gray-850 dark:text-white shadow-lg border border-gray-50 dark:border-gray-850"
		transition={flyAndScale}
		side={$mobile ? 'bottom' : 'bottom-start'}
		sideOffset={3}
	>
		<!-- Header with shortcut and search -->
		<div class="border-b border-gray-200 dark:border-gray-700 p-4 space-y-2">
			{#if searchEnabled}
				<div class="flex items-center gap-2.5">
					<Search className="size-4 text-gray-400" strokeWidth="2.5" />
					<input
						id="model-search-input"
						bind:value={searchValue}
						class="w-full text-sm bg-transparent outline-hidden placeholder-gray-400"
						placeholder={searchPlaceholder}
						autocomplete="off"
					/>
				</div>
			{/if}
			<div class="flex items-center mt-1">
				<button
					class="flex justify-between w-full font-medium line-clamp-1 select-none items-center rounded-button py-2 px-3 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg cursor-pointer data-highlighted:bg-muted"
					on:click={async () => {
						hideLockedModels = !hideLockedModels;
					}}
				>
					<div class="flex gap-2.5 items-center">
						<EyeSlash className="size-4" strokeWidth="2.5" />
						{$i18n.t(`Hide locked models`)}
					</div>

					<div>
						<Switch state={hideLockedModels} />
					</div>
				</button>
			</div>
		</div>

		<div class="flex {$mobile ? 'flex-col' : 'flex-row'} min-h-[400px] max-h-[500px]">
			{#if $mobile}
				<!-- H-scrollable vendor bar (top) -->
				<div
					class="shrink-0 bg-white dark:bg-gray-850
	            flex overflow-x-auto no-scrollbar
	            snap-x snap-mandatory border-b border-gray-200 dark:border-gray-700"
				>
					{#each vendors as vendor, index}
						<button
							class="shrink-0 px-4 py-3 flex flex-col items-center gap-1
				       transition-colors
				       {index === selectedVendorIdx
								? 'text-teal-500 dark:text-teal-400 border-b-2 border-teal-500'
								: 'text-gray-400 dark:text-gray-500'}"
							on:click={() => {
								selectedVendorIdx = index;
								selectedModelIdx = 0;
							}}
						>
							<span class="text-lg">{vendor.icon}</span>
							<span class="text-xs font-medium truncate max-w-[5rem]">
								{vendor.name.replace('★ ', '')}
							</span>
							<div
								class="text-xs {index === selectedVendorIdx
									? 'text-teal-600 dark:text-teal-400'
									: 'text-gray-500 dark:text-gray-500'}"
							>
								({vendor.count})
							</div>
						</button>
					{/each}
				</div>
			{/if}

			<!-- Left sidebar - Vendor tabs -->
			<div
				class="{!$mobile &&
					'w-32 md:w-36'} hidden sm:block border-r border-gray-200 dark:border-gray-700 py-2"
			>
				{#each vendors as vendor, index}
					<button
						class="w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors {index ===
						selectedVendorIdx
							? 'bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300'
							: 'text-gray-600 dark:text-gray-400'}"
						on:click={() => {
							selectedVendorIdx = index;
							selectedModelIdx = 0;
						}}
					>
						<span class="text-base">{vendor.icon}</span>
						<div class="flex-1 min-w-0">
							<div class="truncate font-medium">{vendor.name.replace('★ ', '')}</div>
							<div
								class="text-xs {index === selectedVendorIdx
									? 'text-teal-600 dark:text-teal-400'
									: 'text-gray-500 dark:text-gray-500'}"
							>
								({vendor.count})
							</div>
						</div>
						{#if index === selectedVendorIdx}
							<div class="w-1 h-4 bg-teal-500 rounded-full"></div>
						{/if}
					</button>
				{/each}
			</div>

			<!-- Right panel - Models list -->
			<div
				class="flex-1 py-2 overflow-y-auto"
				on:touchstart|passive={handleTouchStart}
				on:touchend|passive={handleTouchEnd}
			>
				{#if selectedVendor}
					<div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
						<h3 class="font-medium text-gray-900 dark:text-white">{selectedVendor.name}</h3>
					</div>

					{#each filteredModels as item, index}
						{@const isSelected = value === item.value}
						{@const canUse = $user?.role === 'admin' || item.model.can_use === true}
						{@const profile_image = item.model?.info?.meta?.profile_image_url !== "/static/favicon.png" ? item.model?.info?.meta?.profile_image_url : getLogoForModel(getCompanyName(item.model)) }

						<Tooltip content={!canUse ? 'Upgrade your plan to use this model' : ''}>
							<button
								id={'model-item-' + index}
								class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors {index ===
								selectedModelIdx
									? 'bg-teal-50 dark:bg-teal-900/20'
									: ''} {isSelected ? 'bg-teal-50 dark:bg-teal-900/20' : ''}"
								class:locked={!canUse}
								tabindex={canUse ? 0 : -1}
								on:click={() => selectModel(item)}
								use:collect={index}
							>
								<div class="flex-col lg:flex-row items-center justify-between">
									<div class="flex items-center justify-between gap-3 min-w-0 flex-1">
										<div class="flex items-center gap-2 min-w-0 flex-1">
											<div class="flex items-center gap-2">
												<!--{#if isSelected}-->
												<!--	<div class="w-2 h-2 bg-teal-500 rounded-full"></div>-->
												<!--{/if}-->
												<img
													src={profile_image}
													alt="Logo for {item.model.name}"
													class="rounded-full size-10 mr-2"
												/>
											</div>
											{#if !canUse}
												<LockClosed className="size-4 text-gray-400" strokeWidth="2" />
											{/if}
											<div>
												<div class="font-medium text-gray-900 dark:text-white truncate">
													{formatModelName(item.label)}
												</div>

												<!-- Model specs (right-aligned) -->
												<!--{#if getModelSpeciality(item.model)}-->
												<!--	<div class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">-->
												<!--		{specs.tag} — {specs.description}-->
												<!--	</div>-->
												<!--{/if}-->

												{#if item.tags && item.tags.length > 0}
													<div class="flex items-center gap-2 my-1">
														{#each item.tags as tag}
															<span
																class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300"
															>
																{tag.name}
															</span>
														{/each}
													</div>
												{/if}
												{#if item.description}
													<div class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
														{item.description}
													</div>
												{/if}
											</div>
										</div>
										{#if !canUse}
											<span
												class="ml-auto inline-flex items-center rounded-full bg-teal-600/20
										 px-2 py-0.5 text-xs font-semibold dark:text-teal-300 text-teal-500
										 group-hover:bg-teal-600/30 motion-safe:animate-pulse"
											>
												Unlock
											</span>
										{/if}
										{#if isSelected && canUse}
											<Check className="size-5 text-teal-500 flex-shrink-0" strokeWidth="2" />
										{/if}
									</div>
								</div>
							</button>
						</Tooltip>
					{:else}
						<div class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
							{searchValue ? 'No matching models found' : 'No models available'}
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Footer with keyboard shortcuts -->
		<div
			class="border-t border-gray-200 dark:border-gray-700 px-4 py-2 text-xs text-gray-500 dark:text-gray-400"
		>
			{#if showTemporaryChatControl}
				<div class="flex items-center mt-1 mb-2">
					<button
						class="flex justify-between w-full font-medium line-clamp-1 select-none items-center rounded-button py-2 px-3 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg cursor-pointer data-highlighted:bg-muted"
						on:click={async () => {
							temporaryChatEnabled.set(!$temporaryChatEnabled);
							await goto('/');
							const newChatButton = document.getElementById('new-chat-button');
							setTimeout(() => {
								newChatButton?.click();
							}, 0);

							// add 'temporary-chat=true' to the URL
							if ($temporaryChatEnabled) {
								history.replaceState(null, '', '?temporary-chat=true');
							} else {
								history.replaceState(null, '', location.pathname);
							}

							show = false;
						}}
					>
						<div class="flex gap-2.5 items-center">
							<ChatBubbleOval className="size-4" strokeWidth="2.5" />

							{$i18n.t(`Temporary Chat`)}
						</div>

						<div>
							<Switch state={$temporaryChatEnabled} />
						</div>
					</button>
				</div>
			{/if}

			{#if $mobile}
				<!-- NEW: swipe tip -->
				<div class="px-2">← → Swipe sideways to change vendor</div>
			{:else}
				<div class="px-2">← → switch vendor • ↑↓ within list • ↵ select • Esc close</div>
			{/if}
		</div>
	</DropdownMenu.Content>
</DropdownMenu.Root>

<style>
    /* global.css or <style> block */
    .no-scrollbar::-webkit-scrollbar {
        display: none;
    }

    .no-scrollbar {
        -ms-overflow-style: none;
        scrollbar-width: none;
    }

    .locked {
        @apply opacity-50;
    }
</style>
