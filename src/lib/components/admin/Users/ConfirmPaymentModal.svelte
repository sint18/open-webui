<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { confirmPaymentOrder } from '$lib/apis/billing';  // points to /billing/index.ts
	import Modal from '$lib/components/common/Modal.svelte';

  export let orderId: string;

  const dispatch = createEventDispatcher();
  let isLoading = false;
  let errorMessage = '';

  async function handleConfirm() {
    isLoading = true;
    errorMessage = '';
    if (!orderId) return;

    console.log(orderId);

    try {
      await confirmPaymentOrder(localStorage.token, orderId);
      // Notify parent that payment was confirmed
      dispatch('confirmed', { orderId: orderId });
      // Close the modal
      dispatch('close');
    } catch (err) {
      errorMessage = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  function handleCancel() {
    dispatch('close');
  }
</script>

<!-- Replace `<Modal>` with your actual modal wrapper component -->
<Modal>
  <div class="space-y-4">
		<div class="text-lg font-medium self-center">Confirm Payment</div>
    <p>Are you sure you want to confirm payment for order <strong>{orderId}</strong>?</p>

    {#if errorMessage}
      <p class="text-red-600">{errorMessage}</p>
    {/if}

    <div class="flex justify-end space-x-2">
      <button
        type="button"
        on:click={handleCancel}
        disabled={isLoading}
      >
        Cancel
      </button>

      <button
        type="button"
        on:click={handleConfirm}
        disabled={isLoading}
				class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center"
      >
        {#if isLoading}
          Confirming…
        {:else}
          Confirm Payment
        {/if}
      </button>
    </div>
  </div>
</Modal>
