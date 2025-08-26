<script lang="ts">
        import { getContext } from 'svelte';
        import { toast } from 'svelte-sonner';
        import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

        const i18n = getContext('i18n');

        let showDialog = false;

        const handleToast = () => {
                toast.info($i18n.t('This is a placeholder'));
        };
</script>

<div class="space-y-4 text-gray-800 dark:text-gray-200">
        <h1 class="text-2xl font-semibold">{$i18n.t('Reports')}</h1>
        <div class="flex gap-2">
                <button
                        class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200"
                        on:click={handleToast}
                >{$i18n.t('Show Toast')}</button>
                <button
                        class="px-3 py-1 rounded-md bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200"
                        on:click={() => (showDialog = true)}
                >{$i18n.t('Show Dialog')}</button>
        </div>
        <ConfirmDialog bind:show={showDialog} title={$i18n.t('Example Dialog')} />
</div>
