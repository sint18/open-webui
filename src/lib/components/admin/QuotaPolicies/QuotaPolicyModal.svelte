<script lang="ts">
  import Modal from '$lib/components/common/Modal.svelte';
  import { createEventDispatcher } from 'svelte';
  import { createQuotaPolicy, updateQuotaPolicy } from '$lib/apis/quota-policies';
  import { getUsers, getUserById } from '$lib/apis/users';
  import { models } from '$lib/stores';
  import type { QuotaPolicy } from '$lib/types';
  import type { Plan } from '$lib/types/plans';
  import { toast } from 'svelte-sonner';
  import Selector from '$lib/components/common/Selector.svelte';
  import Search from '$lib/components/icons/Search.svelte';
  import dayjs from 'dayjs';
  import ModelSelector from '$lib/components/chat/ModelSelector.svelte';
  import Combobox from '$lib/components/common/Combobox.svelte';

  export let show = false;
  export let policy: QuotaPolicy | null = null;
  export let plans: Plan[] = [];

  const dispatch = createEventDispatcher();

  const defaultForm: QuotaPolicy = {
    id: '',
    user_id: undefined,
    plan_id: undefined,
    resource_pattern: '',
    limit: 0,
    window: 'day',
    effective_from: dayjs().unix(),
    expires_at: undefined
  };

  type ResourceType = 'model' | 'upload' | 'image';

  let form: QuotaPolicy = { ...defaultForm };
  let userInput = '';
  let bulkMode = false;
  let selectedModels: string[] = [];

  let resourceType: ResourceType = 'model';
  let modelValue = '*';
  let uploadValue = '';
  let imageValue = '';
  let modelSearch = '';

  $: modelItems = [{ value: '*', label: '*' }, ...$models.map((m) => ({ value: m.id, label: `${m.name} (${m.id})` }))];
  $: filteredModelItems = modelSearch
    ? modelItems.filter((i) => i.label.toLowerCase().includes(modelSearch.toLowerCase()))
    : modelItems;
  $: if (selectedModels.includes('*')) {
    selectedModels = ['*'];
  }

  function setForm(p: QuotaPolicy | null) {
    if (p) {
      form = { ...p };
      userInput = p.user_id ?? '';
      const [type, value] = (p.resource_pattern || '').split(':');
      resourceType = (type as any) || 'model';
      if (resourceType === 'model') {
        modelValue = value || '*';
      } else if (resourceType === 'upload') {
        uploadValue = value || '';
      } else if (resourceType === 'image') {
        imageValue = value || '';
      }
      bulkMode = false;
      selectedModels = [];
    } else {
      form = { ...defaultForm };
      userInput = '';
      resourceType = 'model';
      modelValue = '*';
      uploadValue = '';
      imageValue = '';
      bulkMode = false;
      selectedModels = [];
    }
  }

  $: setForm(policy);

  async function save() {
    try {
      let user_id = form.user_id;
      if (userInput) {
        if (userInput.includes('@')) {
          const res = await getUsers(localStorage.token, userInput).catch(() => null);
          if (res && res.users && res.users.length > 0) {
            user_id = res.users[0].id;
          } else {
            throw 'User not found';
          }
        } else {
          const u = await getUserById(localStorage.token, userInput);
          user_id = u.id;
        }
      }
      const basePayload = {
        user_id,
        plan_id: form.plan_id,
        limit: form.limit,
        window: form.window,
        effective_from: form.effective_from,
        expires_at: form.expires_at
      };
      if (resourceType === 'model') {
        if (bulkMode && selectedModels.length > 0 && !policy) {
          for (const m of selectedModels) {
            const payload = { ...basePayload, resource_pattern: `model:${m}` };
            const saved = await createQuotaPolicy(localStorage.token, payload);
            dispatch('saved', saved);
          }
        } else {
          const payload = {
            ...basePayload,
            resource_pattern: `model:${modelValue}`
          };
          let saved: QuotaPolicy;
          if (policy) {
            saved = await updateQuotaPolicy(localStorage.token, policy.id, payload);
          } else {
            saved = await createQuotaPolicy(localStorage.token, payload);
          }
          dispatch('saved', saved);
        }
      } else {
        const value = resourceType === 'upload' ? uploadValue : imageValue;
        const payload = {
          ...basePayload,
          resource_pattern: `${resourceType}:${value}`
        };
        let saved: QuotaPolicy;
        if (policy) {
          saved = await updateQuotaPolicy(localStorage.token, policy.id, payload);
        } else {
          saved = await createQuotaPolicy(localStorage.token, payload);
        }
        dispatch('saved', saved);
      }
      show = false;
    } catch (e) {
      toast.error(`${e}`);
    }
  }
</script>

<Modal bind:show>
  <div class="p-4 space-y-4 text-gray-900 dark:text-gray-100">
    <h2 class="text-lg font-semibold">{policy ? 'Edit Quota Policy' : 'Add Quota Policy'}</h2>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">User Email or ID</label>
      <input
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={userInput}
        placeholder="Enter user email or ID" />
    </div>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Plan</label>
      <select
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.plan_id}>
        <option value="">None</option>
        {#each plans as p}
          <option value={p.id}>{p.name} ({p.id})</option>
        {/each}
      </select>
    </div>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Resource Type</label>
      <select
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={resourceType}>
        <option value="model">model</option>
        <option value="upload">upload</option>
        <option value="image">image</option>
      </select>
    </div>

    {#if resourceType === 'model'}
      {#if !policy}
        <div class="flex items-center gap-2">
          <input
            id="bulk"
            type="checkbox"
            class="h-4 w-4 text-blue-600 border-gray-300 rounded"
            bind:checked={bulkMode} />
          <label for="bulk" class="text-sm text-gray-700 dark:text-gray-300">Bulk add models</label>
        </div>
      {/if}

      {#if bulkMode && !policy}
        <div class="space-y-2">
          <label class="block text-sm text-gray-700 dark:text-gray-300">Models</label>
          <div class="space-y-2">
            <div class="flex items-center gap-2 p-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800">
              <Search class="size-4 text-gray-500" />
              <input
                class="flex-1 bg-transparent outline-none text-gray-900 dark:text-gray-100"
                placeholder="Search models"
                bind:value={modelSearch} />
            </div>
            <div class="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800">
              {#each filteredModelItems as item}
                <label class="flex items-center gap-2 p-1 text-gray-900 dark:text-gray-100">
                  <input type="checkbox" value={item.value} bind:group={selectedModels} />
                  {item.label}
                </label>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <div class="space-y-2">
          <label class="block text-sm text-gray-700 dark:text-gray-300">Model</label>
<!--          <Selector bind:value={modelValue} items={modelItems} placeholder="Select a model" searchPlaceholder="Search models" />-->
          <Selector bind:selectedModels={selectedModels} showSetDefault={false}></Selector>
        </div>
      {/if}
    {:else if resourceType === 'upload'}
      <div class="space-y-2">
        <label class="block text-sm text-gray-700 dark:text-gray-300">Upload</label>
        <input
          class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          bind:value={uploadValue}
          placeholder="Enter upload pattern" />
      </div>
    {:else if resourceType === 'image'}
      <div class="space-y-2">
        <label class="block text-sm text-gray-700 dark:text-gray-300">Image</label>
        <input
          class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          bind:value={imageValue}
          placeholder="Enter image pattern" />
      </div>
    {/if}

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Limit</label>
      <input
        type="number"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.limit} />
    </div>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Window</label>
      <select
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        bind:value={form.window}>
        <option value="3h">3h</option>
        <option value="12h">12h</option>
        <option value="day">day</option>
        <option value="week">week</option>
        <option value="month">month</option>
      </select>
    </div>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Effective From</label>
      <input
        type="datetime-local"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        value={new Date(form.effective_from * 1000).toISOString().slice(0, 16)}
        on:change={(e) => {
          const value = e.target.value;
          form.effective_from = value ? dayjs(value).unix() : form.effective_from;
        }} />
    </div>

    <div class="space-y-2">
      <label class="block text-sm text-gray-700 dark:text-gray-300">Expires At</label>
      <input
        type="datetime-local"
        class="w-full p-2 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        value={form.expires_at ? new Date(form.expires_at * 1000).toISOString().slice(0, 16) : ''}
        on:change={(e) => {
          const value = e.target.value;
          form.expires_at = value ? dayjs(value).unix() : undefined;
        }} />
    </div>

    <div class="flex justify-end gap-2 pt-2">
      <button
        class="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        on:click={() => (show = false)}>
        Cancel
      </button>
      <button
        class="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
        on:click={save}>
        Save
      </button>
    </div>
  </div>
</Modal>
