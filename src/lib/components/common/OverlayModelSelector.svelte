<script lang="ts">
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import Fuse from 'fuse.js';

	import { models, mobile, user, type Model } from '$lib/stores';
	import {
		getCompanyName,
		getLogoForModel,
		getModelSpeciality,
		formatModelName,
		getVendorIcon
	} from '$lib/utils/helper-functions';
	import { goto } from '$app/navigation';

	import Modal from '$lib/components/common/Modal.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import X from '$lib/components/icons/XMark.svelte';
	import Star from '$lib/components/icons/Star.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import { ANALYTICS_EVENTS, trackEvent } from '$lib/utils/analytics';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
	export let items: {
		label: string;
		value: string;
		model: Model;
		icon?: string;
		featured?: boolean;
		[key: string]: any;
	}[] = [];

	let searchValue = '';
	let dontShowAgain = false;

	// Load "don't show again" preference on mount
	onMount(() => {
		dontShowAgain = localStorage.getItem('chatbotOverlay.dontShowAgain') === 'true';
	});


	$: filteredItems = (() => {
		// let baseItems = items.filter((item) => $user?.role === 'admin' || item.model.can_use !== false);
		let baseItems = items;
		if (searchValue) {
			const fuse = new Fuse(baseItems, {
				keys: ['value', 'label', 'model.name'],
				threshold: 0.3
			});
			baseItems = fuse.search(searchValue).map((e) => e.item);
		}

		return baseItems;
	})();

	// how many items to show initially (and per “load more”)
	let visibleCount = 20;

	// bump visibleCount by 20 when clicking “Load more”
	function loadMore() {
		visibleCount += 20;
	}

	$: groupedItems = (() => {
		const groups = new Map();

		// Separate featured items
		const featuredItems = filteredItems.filter((item) => item.featured);
		const regularItems = filteredItems.filter((item) => !item.featured);

		// Add featured group if there are featured items
		if (featuredItems.length > 0) {
			groups.set('⭐ Featured', {
				name: '⭐ Featured',
				icon: '⭐',
				items: featuredItems.sort((a, b) => a.label.localeCompare(b.label)),
				priority: 0
			});
		}

		// Group regular items by vendor
		regularItems.forEach((item) => {
			const vendor = getCompanyName(item.model);
			if (!groups.has(vendor)) {
				groups.set(vendor, {
					name: vendor,
					icon: getVendorIcon(vendor),
					items: [],
					priority: vendor === 'Custom Bots' ? 1 : 2
				});
			}
			groups.get(vendor).items.push(item);
		});

		// Sort items within each group
		groups.forEach((group) => {
			group.items.sort((a, b) => a.label.localeCompare(b.label));
		});

		// Convert to array and sort by priority
		return Array.from(groups.values()).sort((a, b) => a.priority - b.priority);
	})();

	$: paginatedGroups = (() => {
    const out = [];
    let count = 0;
    for (const group of groupedItems) {
      if (count >= visibleCount) break;
      out.push(group);
      count += group.items.length;
    }
    return out;
  })();

  // total number of items (for "has more?" check)
  $: totalItemCount = groupedItems.reduce((sum, g) => sum + g.items.length, 0);


	function selectChatbot(item: any) {

		// Track model selection
		trackEvent(ANALYTICS_EVENTS.MODEL_SELECTOR_CLICKED, {
			user_id: $user?.id,
			selected_model: item.value,
			selected_model_name: item.label,
			context: 'model_selected',
			vendor: getCompanyName(item.model)
		});

		// Update recent models
		const recent = JSON.parse(localStorage.getItem('recentModels') || '[]');
		const updated = [item.value, ...recent.filter((v) => v !== item.value)].slice(0, 5);
		localStorage.setItem('recentModels', JSON.stringify(updated));

		// Save "don't show again" preference
		if (dontShowAgain) {
			localStorage.setItem('chatbotOverlay.dontShowAgain', 'true');
		}

		dispatch('select', item);
		show = false;
	}

	function closeModal() {
		if (dontShowAgain) {
			localStorage.setItem('chatbotOverlay.dontShowAgain', 'true');
		}
		show = false;
	}

	function skipModal() {
		if (dontShowAgain) {
			localStorage.setItem('chatbotOverlay.dontShowAgain', 'true');
		}
		dispatch('skip');
		show = false;
	}

	function handleDontShowAgainChange(event) {
		dontShowAgain = event.detail;
		if (dontShowAgain) {
			localStorage.setItem('chatbotOverlay.dontShowAgain', 'true');
		} else {
			localStorage.removeItem('chatbotOverlay.dontShowAgain');
		}
	}
</script>

<Modal
	bind:show
	size="2xl"
	containerClassName="p-4 h-[80vh] fixed inset-0 z-50 bg-black/60 backdrop-blur-sm backdrop-saturate-150 flex items-center justify-center transition-opacity duration-300 opacity-100"
	className="bg-white dark:bg-gray-900 rounded-2xl overflow-hidden"
>
	<!-- Header -->
	<div class="border-b border-gray-200 dark:border-gray-700 p-6">
		<div class="flex items-center justify-between mb-4">
			<div>
				<h1 class="text-2xl font-semibold text-teal-600 dark:text-teal-400">
					{$i18n.t('Choose a Chatbot')}
				</h1>
				<p class="text-gray-600 dark:text-gray-400 text-sm mt-1">
					{$i18n.t('Select a model to start your conversation')}
				</p>
			</div>
			<button
				class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
				on:click={closeModal}
			>
				<X className="size-5 text-gray-500" />
			</button>
		</div>

		<!-- Search -->
		<div class="relative">
			<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 size-4 text-gray-400" />
			<input
				bind:value={searchValue}
				placeholder={$i18n.t('Search models and chatbots...')}
				class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
				autocomplete="off"
			/>
		</div>
	</div>
	<!-- Add this alert block just below your Header (e.g. right before the Search) -->
	{#if items.some(item => item.model.can_use === false)}
		<div
			class="p-4 bg-teal-50 dark:bg-teal-900/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
			<div>
				<h2 class="text-lg font-semibold text-teal-700 dark:text-teal-300">
					{$i18n.t('Unlock • Premium Models')}
				</h2>
				<p class="text-sm text-teal-600 dark:text-teal-400">
					{$i18n.t('Upgrade your plan to access locked chatbots and models.')}
				</p>
			</div>
			<button
				class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-full text-sm font-medium transition"
				on:click={() => goto('/pricing')}
			>
				{$i18n.t('Upgrade Now')}
			</button>
		</div>
	{/if}


	<!-- Content -->
	<div class="overflow-y-auto h-[60vh] p-6">
		{#each paginatedGroups as group}
			<div class="mb-8">
				<div class="flex items-center gap-2 mb-4">
					<span class="text-lg">{group.icon}</span>
					<h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">{group.name}</h2>
					<div class="text-sm text-gray-500 dark:text-gray-400">({group.items.length})</div>
				</div>

				<div class="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each group.items as item}
						{@const canUse = $user?.role === 'admin' || item.model.can_use !== false}
						{@const profile_image = item.model?.info?.meta?.profile_image_url !== "/static/favicon.png" ? item.model?.info?.meta?.profile_image_url : getLogoForModel(getCompanyName(item.model)) }

						<button
							class="group relative bg-gray-50 dark:bg-gray-800 rounded-xl p-4 text-left transition-all duration-200 border border-gray-200 dark:border-gray-700 hover:border-teal-300 dark:hover:border-teal-600 hover:shadow-md
           {!canUse ? 'opacity-50' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}"
							on:click={() => selectChatbot(item)}
							title={formatModelName(item.label)}
							disabled={!canUse}
						>
							{#if item.featured}
								<div class="absolute -top-2 -right-2">
									<div
										class="bg-teal-500 text-white text-xs font-semibold px-2 py-1 rounded-full shadow-sm flex items-center gap-1"
									>
										<Star className="size-3" />
										{$i18n.t('Featured')}
									</div>
								</div>
							{/if}

							<div class="flex items-start gap-3">
								<div class="flex-shrink-0">
									<img
										src={profile_image}
										alt="Logo for {item.model.name}"
										class="rounded-full size-20"
									/>
								</div>

								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2 mb-1">
										{#if !canUse}
											<LockClosed className="size-4 text-gray-400" strokeWidth="2" />
										{/if}
										<h3 class="font-medium text-gray-900 dark:text-gray-100 truncate">
											{formatModelName(item.label)}
										</h3>
									</div>

									{#if item.tags && item.tags.length > 0}
										<div class="flex items-center gap-2 mb-2">
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
										<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
											{item.description}
										</p>
									{/if}
								</div>

								<div class="flex-shrink-0">
									{#if !canUse}
										<span
											class="ml-auto inline-flex items-center rounded-full bg-teal-600/20
										 px-2 py-0.5 text-xs font-semibold dark:text-teal-300 text-teal-500
										 group-hover:bg-teal-600/30 motion-safe:animate-pulse"
										>
											{$i18n.t('Unlock')}
										</span>
									{:else}
										<div
											class="p-2 rounded-full bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400 group-hover:bg-teal-100 dark:group-hover:bg-teal-900/40 transition-colors"
										>
											<ChevronRight className="size-4" />
										</div>
									{/if}
								</div>
							</div>
						</button>
					{/each}
				</div>
			</div>
		{:else}
			<div class="text-center py-12">
				<div class="text-gray-400 text-6xl mb-4">🤖</div>
				<p class="text-gray-600 dark:text-gray-400">
					{searchValue ? $i18n.t('No matching chatbots found') : $i18n.t('No chatbots available')}
				</p>
			</div>
		{/each}
		<!-- inside your scrollable content, after the {#each groupedItems …} block -->
		{#if totalItemCount > visibleCount}
			<div class="flex justify-center mt-4">
				<button
					class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-full text-sm font-medium transition"
					on:click={loadMore}
				>
					{$i18n.t('Load more')}
				</button>
			</div>
		{/if}
	</div>

	<!-- Footer -->
	<div class="border-t border-gray-200 dark:border-gray-800 p-6 bg-gray-50 dark:bg-gray-900">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<label
					class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer"
				>
					<Switch bind:state={dontShowAgain} on:change={handleDontShowAgainChange} />
					{$i18n.t("Don't show again")}
				</label>
			</div>

			<div class="flex items-center gap-3">
				<button
					class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
					on:click={skipModal}
				>
					{$i18n.t('Skip')}
				</button>
			</div>
		</div>
	</div>
</Modal>

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
