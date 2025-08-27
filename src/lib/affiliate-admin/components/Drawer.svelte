<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';

  export let show = false;
  export let className = '';
  export let onClose: () => void = () => {};

  let modalElement: HTMLDivElement | null = null;

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      show = false;
    }
  };

  onMount(() => {
    if (show && modalElement) {
      document.body.appendChild(modalElement);
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
  });

  $: if (!show && modalElement && document.body.contains(modalElement)) {
    document.body.removeChild(modalElement);
    window.removeEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'unset';
    onClose();
  } else if (show && modalElement && !document.body.contains(modalElement)) {
    document.body.appendChild(modalElement);
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
  }

  onDestroy(() => {
    if (modalElement && document.body.contains(modalElement)) {
      document.body.removeChild(modalElement);
    }
    window.removeEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'unset';
  });
</script>

{#if show}
<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<div
  bind:this={modalElement}
  class="fixed inset-0 bg-black/60 flex justify-end z-50"
  in:fade={{ duration: 100 }}
  on:mousedown={() => (show = false)}
>
  <div
    class="w-full max-w-md h-full bg-white dark:bg-gray-900 overflow-y-auto {className}"
    in:fly={{ x: 200, duration: 150 }}
    on:mousedown|stopPropagation
  >
    <slot />
  </div>
</div>
{/if}
