<script lang="ts">
	import { getContext } from 'svelte';
	import CheckCircle from '$lib/components/icons/Check.svelte'; // adjust path if necessary

	const i18n = getContext('i18n');

	interface Plan {
		name: string;
		tagline: string;
		price: number;
		interval: string; // "m" or "y" etc.
		cta: string; // button label
		features: string[];
		highlight?: boolean; // for future use (e.g. featured tier)
	}

	const plans: Plan[] = [
		{
			name: 'Starter',
			tagline: 'For individuals just getting started',
			price: 29,
			interval: 'm',
			cta: 'Get started',
			features: [
				'Unlimited chats',
				'1 active chatbot',
				'Community support',
				'Pause or cancel anytime'
			]
		},
		{
			name: 'Pro',
			tagline: 'For power users & small teams',
			price: 59,
			interval: 'm',
			cta: 'Get started',
			features: [
				'Unlimited chats',
				'3 active chatbots',
				'Priority support',
				'Pause or cancel anytime'
			],
			highlight: true
		},
		{
			name: 'Studio',
			tagline: 'For organisations & advanced workflows',
			price: 99,
			interval: 'm',
			cta: 'Contact sales',
			features: [
				'Unlimited chats & bots',
				'Custom branding',
				'Dedicated account manager',
				'Enterprise‑grade SLA'
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
					class="flex flex-col rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-8 shadow-sm"
				>
					<div class="mb-6">
						<h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">{plan.name}</h2>
						<p class="text-sm text-gray-600 dark:text-gray-400">{plan.tagline}</p>
					</div>

					<div class="mb-6">
						<span class="text-4xl font-semibold text-gray-900 dark:text-white">${plan.price}</span>
						<span class="text-base font-medium text-gray-600 dark:text-gray-400"
							>/{plan.interval}</span
						>
					</div>

					<a
						href="#"
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
