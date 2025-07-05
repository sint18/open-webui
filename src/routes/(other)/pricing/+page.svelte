<script lang="ts">
	import { getContext } from 'svelte';
	import CheckCircle from '$lib/components/icons/Check.svelte'; // adjust path if necessary

	const i18n = getContext('i18n');

	interface Plan {
		name: string;
		tagline: string;
		price: number;
		credits: number; // Add credits field
		interval: string; // "m" or "y" etc.
		cta: string; // button label
		features: string[];
		highlight?: boolean; // for future use (e.g. featured tier)
	}

	const plans: Plan[] = [
		{
			name: 'Starter',
			tagline: 'For individuals just getting started',
			price: 30000,
			credits: 750,
			interval: 'month',
			cta: 'Get started',
			features: [
				'Unlimited chats',
				'GPT-4o-mini, GPT-4.1-mini, Gemini 2.5 Flash',
				'DeepSeek-chat V3, Mistral Small 3.1, Llama-3/4 and more models in the future',
				'Community support',
				'Basic chat interface',
				'Pause or cancel anytime'
			]
		},
		{
			name: 'Pro',
			tagline: 'For power users & small teams',
			price: 55000,
			credits: 1500,
			interval: 'month',
			cta: 'Get started',
			features: [
				'All Starter models & features plus',
				'GPT-4o-full, GPT-4.1-full, Gemini 2.5 Pro, Claude 3.5 Sonnet',
				'DeepSeek-Reasoner R1, Mistral Medium 3, Llama-4 Maverick',
				'Advanced features',
				'Priority support',
				'Pause or cancel anytime'
			],
			highlight: true
		},
		{
			name: 'Studio',
			tagline: 'For organisations & advanced workflows',
			price: 125000,
			credits: 4500,
			interval: 'month',
			cta: 'Get started',
			features: [
				'Unlimited chats & bots',
				'All Pro models & features plus',
				'Claude 3.7 Sonnet, Claude Opus 4, OpenAI o3, GPT-4o-Vision',
				'Mixtral 8×22B, Llama-4 Maverick-LongCtx, Llama-3 70B',
				'24/7 priority support',
				'Pause or cancel anytime'
			]
		}
	];
</script>

<section class="w-full">
	<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-12">
		<h1 class="text-center text-3xl md:text-4xl font-semibold mb-2 text-gray-900 dark:text-gray-50">
			{'Plans that scale with you.'}
		</h1>
		<p class="text-center text-gray-600 dark:text-gray-400 mb-10">
			{"Choose a plan that's right for you."}
		</p>

		<div class="grid gap-6 md:grid-cols-3">
			{#each plans as plan}
				<div
					class="flex flex-col rounded-2xl border {plan.highlight
						? 'border-[#21706d] shadow-lg'
						: 'border-gray-200 dark:border-gray-700'} bg-gray-50 dark:bg-gray-900 p-8 {plan.highlight
						? 'shadow-lg'
						: 'shadow-sm'} relative"
					style={plan.highlight
						? 'box-shadow: 0 10px 15px -3px rgba(33, 112, 109, 0.2), 0 4px 6px -4px rgba(33, 112, 109, 0.1);'
						: ''}
				>
					{#if plan.highlight}
						<div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
							<div
								class="text-white text-xs font-semibold px-3 py-1 rounded-full shadow-sm"
								style="background-color: #21706d;"
							>
								Most Popular
							</div>
						</div>
					{/if}
					<div class="mb-6">
						<h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">{plan.name}</h2>
						<p class="text-sm text-gray-600 dark:text-gray-400">{plan.tagline}</p>
					</div>

					<div class="mb-6">
						<span class="text-4xl font-semibold text-gray-900 dark:text-white"
							>MMK {' '}{plan.price}</span
						>
						<span class="text-base font-medium text-gray-600 dark:text-gray-400"
							>/{plan.interval}</span
						>
					</div>

					<a
						href="/checkout?plan={plan.name.toLowerCase()}"
						class="inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-700 focus-visible:ring-2 focus-visible:ring-primary-500"
						>{plan.cta}</a
					>

					<ul class="mt-8 space-y-3 text-sm">
						{#each plan.features as feat}
							<li class="flex items-start gap-3 text-gray-700 dark:text-gray-300">
								<CheckCircle className="size-4 flex-shrink-0 mt-0.5" />
								<span>{feat}</span>
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
	</div>
</section>

<style>
	/* Rely on Tailwind for styling */
</style>
