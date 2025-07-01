<script lang="ts">
	export let currentCredits: number = 0;
	export let totalCredits: number = 0;
	export let showDetails: boolean = true;
	export let size: 'sm' | 'md' | 'lg' = 'md';

	// Calculate percentage
	$: percentage =
		totalCredits > 0 ? Math.max(0, Math.min(100, (currentCredits / totalCredits) * 100)) : 0;
	$: isLow = percentage < 20;
	$: isCritical = percentage < 10;

	// Responsive sizing
	$: heightClass = {
		sm: 'h-1.5',
		md: 'h-2',
		lg: 'h-3'
	}[size];

	$: textClass = {
		sm: 'text-xs',
		md: 'text-sm',
		lg: 'text-base'
	}[size];

	// Color based on remaining credits
	$: progressColor = isCritical
		? 'bg-red-500 dark:bg-red-400'
		: isLow
			? 'bg-yellow-500 dark:bg-yellow-400'
			: 'bg-green-500 dark:bg-green-400';

	$: bgColor = 'bg-gray-200 dark:bg-gray-700';
</script>

<div class="credit-progress-container">
	<!-- {#if showDetails}
		<div class="flex items-center justify-between mb-1">
			<span class="text-gray-700 dark:text-gray-300 font-medium {textClass}">
				Credits Remaining
			</span>
			<span class="text-gray-600 dark:text-gray-400 {textClass}">
				{currentCredits.toLocaleString()} / {totalCredits.toLocaleString()}
			</span>
		</div>
	{/if} -->

	<div class="relative w-full {bgColor} rounded-full {heightClass} overflow-hidden">
		<!-- Progress bar -->
		<div
			class="absolute top-0 left-0 {heightClass} {progressColor} rounded-full transition-all duration-300 ease-out"
			style="width: {percentage}%"
		>
			<!-- Shimmer effect for visual appeal -->
			<div
				class="absolute inset-0 -skew-x-12 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"
			></div>
		</div>

		<!-- Critical warning indicator -->
		{#if isCritical}
			<div class="absolute top-0 right-1 {heightClass} flex items-center">
				<div class="w-1 h-1 bg-red-600 rounded-full animate-pulse"></div>
			</div>
		{/if}
	</div>

	{#if showDetails}
		<div class="flex items-center justify-between mt-1">
			<span class="text-xs text-gray-500 dark:text-gray-400">
				{percentage.toFixed(1)}% remaining
			</span>
			{#if isCritical}
				<span class="text-xs text-red-600 dark:text-red-400 font-medium"> ⚠️ Credits low </span>
			{:else if isLow}
				<span class="text-xs text-yellow-600 dark:text-yellow-400 font-medium">
					⚡ Running low
				</span>
			{/if}
		</div>
	{/if}
</div>

<style>
	@keyframes shimmer {
		0% {
			transform: translateX(-100%) skewX(-12deg);
		}
		100% {
			transform: translateX(200%) skewX(-12deg);
		}
	}

	.animate-shimmer {
		animation: shimmer 2s infinite;
	}
</style>
