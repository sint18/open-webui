<script>
    import { page } from '$app/stores';
    import UserDetails from '$lib/components/admin/Users/UserDetails.svelte';

    const userId = $page.params.id;
</script>

<div class="max-w-4xl mx-auto px-4 py-6">
    <UserDetails {userId} />
</div>