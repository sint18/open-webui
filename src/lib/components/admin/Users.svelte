<script>
	import { getContext, tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';

	import UserList from './Users/UserList.svelte';
	import Groups from './Users/Groups.svelte';
	import Orders from './Settings/Orders.svelte';

	const i18n = getContext('i18n');

	let selectedTab = 'overview';
	let loaded = false;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		}

		loaded = true;

		const containerElement = document.getElementById('users-tabs-container');

		if (containerElement) {
			containerElement.addEventListener('wheel', function (event) {
				if (event.deltaY !== 0) {
					// Adjust horizontal scroll position based on vertical scroll
					containerElement.scrollLeft += event.deltaY;
				}
			});
		}
	});
</script>

<div class="flex flex-col lg:flex-row w-full h-full pb-2 lg:space-x-4">
	<div
		id="users-tabs-container"
		class=" flex flex-row overflow-x-auto gap-2.5 max-w-full lg:gap-1 lg:flex-col lg:flex-none lg:w-40 dark:text-gray-200 text-sm font-medium text-left scrollbar-none"
	>
		<button
			class="px-0.5 py-1 min-w-fit rounded-lg lg:flex-none flex text-right transition {selectedTab ===
			'overview'
				? ''
				: ' text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'}"
			on:click={() => {
				selectedTab = 'overview';
			}}
		>
			<div class=" self-center mr-2">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 16 16"
					fill="currentColor"
					class="size-4"
				>
					<path
						d="M8.5 4.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0ZM10.9 12.006c.11.542-.348.994-.9.994H2c-.553 0-1.01-.452-.902-.994a5.002 5.002 0 0 1 9.803 0ZM14.002 12h-1.59a2.556 2.556 0 0 0-.04-.29 6.476 6.476 0 0 0-1.167-2.603 3.002 3.002 0 0 1 3.633 1.911c.18.522-.283.982-.836.982ZM12 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"
					/>
				</svg>
			</div>
			<div class=" self-center">{$i18n.t('Overview')}</div>
		</button>

		<button
			class="px-0.5 py-1 min-w-fit rounded-lg lg:flex-none flex text-right transition {selectedTab ===
			'groups'
				? ''
				: ' text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'}"
			on:click={() => {
				selectedTab = 'groups';
			}}
		>
			<div class=" self-center mr-2">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 16 16"
					fill="currentColor"
					class="size-4"
				>
					<path
						d="M8 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM3.156 11.763c.16-.629.44-1.21.813-1.72a2.5 2.5 0 0 0-2.725 1.377c-.136.287.102.58.418.58h1.449c.01-.077.025-.156.045-.237ZM12.847 11.763c.02.08.036.16.046.237h1.446c.316 0 .554-.293.417-.579a2.5 2.5 0 0 0-2.722-1.378c.374.51.653 1.09.813 1.72ZM14 7.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0ZM3.5 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM5 13c-.552 0-1.013-.455-.876-.99a4.002 4.002 0 0 1 7.753 0c.136.535-.324.99-.877.99H5Z"
					/>
				</svg>
			</div>
			<div class=" self-center">{$i18n.t('Groups')}</div>
		</button>

		<button
			class="px-0.5 py-1 min-w-fit rounded-lg lg:flex-none flex text-right transition {selectedTab ===
			'orders'
				? ''
				: ' text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'}"
			on:click={() => {
				selectedTab = 'orders';
			}}
		>
			<div class=" self-center mr-2">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-4 h-4"
				>
					<path d="M12 7.5a2.25 2.25 0 1 0 0 4.5 2.25 2.25 0 0 0 0-4.5Z" />
					<path
						fill-rule="evenodd"
						d="M1.5 4.875C1.5 3.839 2.34 3 3.375 3h17.25c1.035 0 1.875.84 1.875 1.875v9.75c0 1.036-.84 1.875-1.875 1.875H3.375A1.875 1.875 0 0 1 1.5 14.625v-9.75ZM8.25 9.75a3.75 3.75 0 1 1 7.5 0 3.75 3.75 0 0 1-7.5 0ZM18.75 9a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75h-.008a.75.75 0 0 1-.75-.75V9.75a.75.75 0 0 1 .75-.75h.008ZM4.5 9.75A.75.75 0 0 1 5.25 9h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H5.25a.75.75 0 0 1-.75-.75V9.75Z"
						clip-rule="evenodd"
					/>
					<path
						d="M2.25 18a.75.75 0 0 0 0 1.5c5.4 0 10.63.722 15.6 2.075 1.19.324 2.4-.558 2.4-1.82V18.75a.75.75 0 0 0-.75-.75H2.25Z"
					/>
				</svg>
			</div>
			<div class=" self-center">{$i18n.t('Orders')}</div>
		</button>
	</div>

	<div class="flex-1 mt-1 lg:mt-0 overflow-y-scroll">
		{#if selectedTab === 'overview'}
			<UserList />
		{:else if selectedTab === 'groups'}
			<Groups />
		{:else if selectedTab === 'orders'}
			<Orders />
		{/if}
	</div>
</div>
