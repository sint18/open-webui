<script lang="ts">
	// pulls in the standard chrome
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Navbar from '$lib/components/layout/Navbar.svelte';
</script>

<!-- full-height flex layout identical to the chat pages -->
<div class="flex h-full w-full overflow-hidden dark:bg-gray-900 bg-white">
	<!-- <Sidebar /> -->
	<!-- collapsible behaviour is inside the component -->
	<div class="flex flex-col flex-1">
		<Navbar initNewChat={() => {}} chat={null} selectedModels={undefined} />
		<div class="flex-1 overflow-y-auto">
			<slot />
			<!-- Pricing content -->
		</div>
	</div>
</div>
