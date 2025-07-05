<script>
	import { goto } from '$app/navigation';
</script>

<div class="flex h-screen w-full overflow-hidden dark:bg-gray-900">
	<!-- <Sidebar /> -->
	<!-- collapsible behaviour is inside the component -->
	<div class="flex flex-col flex-1">
		<!--		<Navbar initNewChat={() => {}} chat={null} selectedModels={undefined} showModelSelector={false}/>-->
		<div class="flex-1 overflow-y-auto relative">
			<!-- Close button -->
			<button
				on:click={() => goto('/')}
				class="absolute top-4 right-4 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				aria-label="Close"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<path d="M18 6L6 18M6 6l12 12" />
				</svg>
			</button>
			<slot></slot>
		</div>
	</div>
</div>
