<script lang="ts">
  import Modal from '$lib/components/common/Modal.svelte';
  import { createEventDispatcher } from 'svelte';
  import { createPlan, updatePlan } from '$lib/apis/plans';
  import type { Plan, PlanType } from '$lib/types/plans';
  import { toast } from 'svelte-sonner';

  export let show = false;
  export let plan: Plan | null = null;

  const dispatch = createEventDispatcher();

  const defaultForm: Plan = {
    id: '',
    name: '',
    description: '',
    price: 0,
    credits: 0,
    image_credits: 0,
    video_credits: 0,
    plan_type: 'subscription' as PlanType,
    features: {},
    is_active: true,
    created_at: 0,
    updated_at: 0
  };

  let form: Plan = { ...defaultForm };
  let featuresText = JSON.stringify(form.features, null, 2);
  let featuresError = '';

  $: if (plan) {
    form = { ...plan };
    featuresText = JSON.stringify(form.features ?? {}, null, 2);
  } else {
    form = { ...defaultForm };
    featuresText = JSON.stringify(form.features ?? {}, null, 2);
  }

  async function save() {
    try {
      let parsedFeatures = {};
      if (featuresText.trim()) {
        try {
          parsedFeatures = JSON.parse(featuresText);
          form.features = parsedFeatures;
          featuresError = '';
        } catch (e) {
          featuresError = 'Invalid JSON';
          throw e;
        }
      }

      let saved: Plan;
      if (plan) {
        saved = await updatePlan(localStorage.token, plan.id, {
          name: form.name,
          description: form.description,
          price: form.price,
          credits: form.credits,
          image_credits: form.image_credits,
          video_credits: form.video_credits,
          plan_type: form.plan_type,
          features: parsedFeatures,
          is_active: form.is_active
        });
      } else {
        saved = await createPlan(localStorage.token, {
          name: form.name,
          description: form.description,
          price: form.price,
          credits: form.credits,
          image_credits: form.image_credits,
          video_credits: form.video_credits,
          plan_type: form.plan_type,
          features: parsedFeatures,
          is_active: form.is_active
        });
      }
      dispatch('saved', saved);
      show = false;
    } catch (e) {
      toast.error(`${e}`);
    }
  }
</script>

<Modal bind:show>
  <div class="p-4 space-y-4 text-gray-900 dark:text-gray-100">
    <h2 class="text-lg font-semibold">{plan ? 'Edit Plan' : 'Add Plan'}</h2>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Name</label>
      <input
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.name}
      />
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Description</label>
      <textarea
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.description}
      ></textarea>
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Price</label>
      <input
        type="number"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.price}
      />
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Credits</label>
      <input
        type="number"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.credits}
      />
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Image Credits</label>
      <input
        type="number"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.image_credits}
      />
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Video Credits</label>
      <input
        type="number"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.video_credits}
      />
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Features (JSON)</label>
      <textarea
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono"
        rows="4"
        bind:value={featuresText}
      ></textarea>
      {#if featuresError}
        <p class="text-sm text-red-500">{featuresError}</p>
      {/if}
    </div>
    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Plan Type</label>
      <select
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.plan_type}
      >
        <option value="subscription">subscription</option>
        <option value="package">package</option>
        <option value="topup">topup</option>
        <option value="custom">custom</option>
      </select>
    </div>
    <div class="space-y-2">
      <label class="inline-flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <input type="checkbox" bind:checked={form.is_active} />
        Active
      </label>
    </div>
    <div class="flex justify-end gap-2 pt-2">
      <button
        class="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        on:click={() => (show = false)}
      >
        Cancel
      </button>
      <button
        class="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
        on:click={save}
      >
        Save
      </button>
    </div>
  </div>
</Modal>

