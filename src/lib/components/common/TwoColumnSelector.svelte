<script lang="ts">
	import Fuse from 'fuse.js';

	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';

	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import Search from '$lib/components/icons/Search.svelte';

	import { getOllamaVersion } from '$lib/apis/ollama';

	import { models, mobile, settings, config, type Model } from '$lib/stores';
	import { getModels } from '$lib/apis';

	import dayjs from '$lib/dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import { getCompanyName, getLogoForModel } from '$lib/utils/helper-functions';
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

	let ollamaVersion = null;

	// Group models by vendor
	$: vendors = (() => {
		const vendorMap = new Map();

		// Add "All Models" vendor first
		vendorMap.set('All Models', {
			name: 'All Models',
			icon: '📋',
			models: items,
			count: items.length
		});

		// Get recent models (last 5 used models from localStorage or based on some criteria)
		const recentModels = getRecentModels();

		// Add "Recent" vendor if there are recent models
		if (recentModels.length > 0) {
			vendorMap.set('★ RECENT', {
				name: '★ RECENT',
				icon: '★',
				models: recentModels,
				count: recentModels.length
			});
		}

		// Group remaining models by vendor
		items.forEach((item) => {
			// if (recentModels.some(recent => recent.value === item.value)) return; // Skip if already in recent

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

		return Array.from(vendorMap.values());
	})();

	$: selectedVendor = vendors[selectedVendorIdx] || vendors[0];
	$: filteredModels = searchValue
		? fuse
				.search(searchValue)
				.map((e) => e.item)
				.filter((item) => selectedVendor.models.some((model) => model.value === item.value))
		: selectedVendor?.models || [];

	const fuse = new Fuse(items, {
		keys: ['value', 'label', 'model.name'],
		threshold: 0.4
	});

	function getRecentModels() {
		// Get recent models from localStorage or some other logic
		const recent = JSON.parse(localStorage.getItem('recentModels') || '[]');
		return items.filter((item) => recent.includes(item.value)).slice(0, 5);
	}

	// function getVendorName(model: Model): string {
	// 	if (model.owned_by === 'ollama') return 'Ollama';
	// 	if (model.owned_by === 'openai' || model.name?.toLowerCase().includes('gpt')) return 'OpenAI';
	// 	if (model.name?.toLowerCase().includes('claude')) return 'Anthropic';
	// 	if (model.name?.toLowerCase().includes('gemini') || model.name?.toLowerCase().includes('palm')) return 'Google';
	// 	if (model.name?.toLowerCase().includes('llama')) return 'Meta';
	// 	if (model.name?.toLowerCase().includes('mistral')) return 'Mistral';
	// 	if (model.name?.toLowerCase().includes('deepseek')) return 'DeepSeek';
	// 	return model.owned_by || 'Other';
	// }

	function getVendorIcon(vendor: string): string {
		switch (vendor.toLowerCase()) {
			case 'openai':
				return '⚡';
			case 'anthropic':
				return '🎭';
			case 'google':
				return '🔍';
			case 'meta':
				return '📘';
			case 'mistral':
				return '🌪️';
			case 'deepseek':
				return '🔬';
			case 'ollama':
				return '🦙';
			default:
				return '🤖';
		}
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

	function formatModelSpecs(model: Model): string {
		const specs = [];

		// Speed indicator
		if (model.name?.toLowerCase().includes('mini') || model.name?.toLowerCase().includes('fast')) {
			specs.push('Fast');
		}

		// Vision capability
		if (model.info?.meta?.vision || model.name?.toLowerCase().includes('vision')) {
			specs.push('Vision ✓');
		}

		// Cost indicator
		if (
			model.name?.toLowerCase().includes('turbo') ||
			model.name?.toLowerCase().includes('cheap')
		) {
			specs.push('Cheap');
		}

		return specs.join(' │ ');
	}

	function formatModelName(modelName: string): string {
		return modelName.split('/').pop() || modelName;
	}

	function selectModel(item: any) {
		value = item.value;

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
				scrollSelectedIntoView()
				break;
			case 'ArrowDown':
				e.preventDefault();
				selectedModelIdx = Math.min(filteredModels.length - 1, selectedModelIdx + 1);
				scrollSelectedIntoView()
				break;
			case 'Enter':
				e.preventDefault();
				if (filteredModels[selectedModelIdx]) {
					selectModel(filteredModels[selectedModelIdx]);
				}
				break;
			case 'Escape':
				e.preventDefault();
				show = false;
				break;
		}
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
		class="z-40 {$mobile
			? 'w-full'
			: className} max-w-[calc(100vw-1rem)] justify-start rounded-xl bg-white dark:bg-gray-850 dark:text-white shadow-lg outline-hidden"
		transition={flyAndScale}
		side={$mobile ? 'bottom' : 'bottom-start'}
		sideOffset={3}
	>
		<!-- Header with shortcut and search -->
		<div class="border-b border-gray-200 dark:border-gray-700 p-4">
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
		</div>

		<div class="flex min-h-[400px] max-h-[500px]">
			<!-- Left sidebar - Vendor tabs -->
			<div class="w-32 md:w-36 border-r border-gray-200 dark:border-gray-700 py-2">
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
			<div class="flex-1 py-2 overflow-y-auto">
				{#if selectedVendor}
					<div class="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
						<h3 class="font-medium text-gray-900 dark:text-white">{selectedVendor.name}</h3>
					</div>

					{#each filteredModels as item, index}
						{@const isSelected = value === item.value}
						<button
							id={"model-item-" + index}
							class="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors {index ===
							selectedModelIdx
								? 'bg-teal-50 dark:bg-teal-900/20'
								: ''} {isSelected ? 'bg-teal-50 dark:bg-teal-900/20' : ''}"
							on:click={() => selectModel(item)}
							use:collect={index}
						>
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-3 min-w-0 flex-1">
									<div class="flex items-center gap-2">
										{#if isSelected}
											<div class="w-2 h-2 bg-teal-500 rounded-full"></div>
										{/if}
										<img
											src={getLogoForModel(getCompanyName(item.model))}
											alt="Logo for {item.model.name}"
											class="rounded-full size-5 mr-2"
										/>
									</div>
									<div class="font-medium text-gray-900 dark:text-white truncate">{item.label}</div>
								</div>

								<!-- Model specs (right-aligned) -->
								{#if formatModelSpecs(item.model)}
									<div class="ml-4 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
										{formatModelSpecs(item.model)}
									</div>
								{/if}
							</div>
						</button>
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
			← → switch vendor • ↑↓ within list • ↵ select • Esc close
		</div>
	</DropdownMenu.Content>
</DropdownMenu.Root>
