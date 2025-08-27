<script lang="ts">
  import DOMPurify from 'dompurify';
  import { onMount, onDestroy } from 'svelte';
  import * as FocusTrap from 'focus-trap';
  import { fade } from 'svelte/transition';
  import { flyAndScale } from '$lib/utils/transitions';
  import { marked } from 'marked';

  export let title = '';
  export let message = '';
  export let cancelLabel = 'Cancel';
  export let confirmLabel = 'Confirm';
  export let onConfirm: () => void | Promise<void> = () => {};
  export let show = false;

  let modalElement: HTMLDivElement | null = null;
  let mounted = false;
  let focusTrap: FocusTrap.FocusTrap | null = null;

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') show = false;
    if (event.key === 'Enter') confirmHandler();
  };

  const confirmHandler = async () => {
    show = false;
    await onConfirm();
  };

  onMount(() => {
    mounted = true;
  });

  $: if (mounted) {
    if (show && modalElement) {
      document.body.appendChild(modalElement);
      focusTrap = FocusTrap.createFocusTrap(modalElement);
      focusTrap.activate();
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    } else if (modalElement) {
      focusTrap && focusTrap.deactivate();
      window.removeEventListener('keydown', handleKeyDown);
      if (document.body.contains(modalElement)) {
        document.body.removeChild(modalElement);
        document.body.style.overflow = 'unset';
      }
    }
  }

  onDestroy(() => {
    if (focusTrap) focusTrap.deactivate();
    if (modalElement && document.body.contains(modalElement)) {
      document.body.removeChild(modalElement);
    }
    document.body.style.overflow = 'unset';
  });
</script>

{#if show}
<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
  bind:this={modalElement}
  class="fixed inset-0 bg-black/60 flex justify-center items-center z-50"
  in:fade={{ duration: 10 }}
  on:mousedown={() => (show = false)}
>
  <div
    class="bg-gray-50 dark:bg-gray-950 rounded-2xl w-full max-w-md mx-2 shadow-3xl"
    in:flyAndScale
    on:mousedown|stopPropagation
  >
    <div class="px-6 py-6 flex flex-col">
      <div class="text-lg font-semibold dark:text-gray-200 mb-2.5">{title || 'Confirm your action'}</div>
      <div class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {@html DOMPurify.sanitize(marked.parse(message || 'This action cannot be undone. Do you wish to continue?'))}
      </div>
      <div class="flex justify-between gap-1.5">
        <button
          class="bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white font-medium w-full py-2.5 rounded-lg transition"
          on:click={() => (show = false)}
        >{cancelLabel}</button>
        <button
          class="bg-gray-900 hover:bg-gray-850 text-gray-100 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-800 font-medium w-full py-2.5 rounded-lg transition"
          on:click={confirmHandler}
        >{confirmLabel}</button>
      </div>
    </div>
  </div>
</div>
{/if}
