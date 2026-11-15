<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import {
  ComboboxRoot,
  ComboboxAnchor,
  ComboboxInput,
  ComboboxTrigger,
  ComboboxContent,
  ComboboxViewport,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxEmpty,
} from 'reka-ui';
import { ApiError, parseErrors } from '../utils/api';
import { showToast } from '../composables/useToast';

interface SelectOption {
  value: string;
  label: string;
}

/** One page of options from `loader`. */
interface LoaderPage {
  results: SelectOption[];
  hasMore?: boolean;
  currentPage?: number;
}

/** What `create` resolves to: the new item, which becomes the selected option and is passed on with `created`. */
interface CreatedItem {
  id: number;
  name: string;
}

const props = withDefaults(
  defineProps<{
    options?: SelectOption[];
    prependOptions?: SelectOption[];
    modelValue?: string | number;
    placeholder?: string;
    // Async loader (e.g. a combined users + teams dropdown). Receives `(q, page)` and resolves to
    // `{ results: [{ value, label }], hasMore: bool, currentPage: int }`.
    loader?: ((q: string, page: number) => Promise<LoaderPage>) | null;
    initialDisplayValue?: string;
    /** Creates an item named after the search text; the option to create one only shows when it's set. */
    create?: (name: string) => Promise<CreatedItem>;
    createLabel?: string;
  }>(),
  {
    options: () => [],
    prependOptions: () => [],
    modelValue: '',
    placeholder: '',
    loader: null,
    initialDisplayValue: '',
    createLabel: 'item',
  },
);

const emit = defineEmits<{ 'update:modelValue': [value: string]; created: [item: CreatedItem] }>();

const query = ref('');
const apiOptions = ref<SelectOption[]>([]);
const currentPage = ref(1);
const hasMore = ref(false);
const isLoadingMore = ref(false);
const currentSearchText = ref('');
const viewportRef = ref(null);
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

const isAsync = computed(() => !!props.loader);

const effectiveOptions = computed(() => {
  const base = isAsync.value ? apiOptions.value : props.options;
  return props.prependOptions.length ? [...props.prependOptions, ...base] : base;
});

const selectedLabel = computed(() => {
  if (!props.modelValue) return '';
  const match = effectiveOptions.value.find((o) => String(o.value) === String(props.modelValue));
  return match?.label || props.initialDisplayValue || '';
});

const CREATE_SENTINEL = '__create_new__';

const creatableOption = computed(() => {
  if (!props.create) return null;
  const q = query.value.trim();
  if (!q) return null;
  const lower = q.toLowerCase();
  const exactMatch = effectiveOptions.value.find((o) => o.label.toLowerCase() === lower);
  if (exactMatch) return null;
  return { value: CREATE_SENTINEL, label: q };
});

const filteredOptions = computed(() => effectiveOptions.value);

async function createItem(name: string) {
  if (!props.create) return;
  try {
    const newItem = await props.create(name);
    const mapped = { value: String(newItem.id), label: newItem.name };
    apiOptions.value = [mapped, ...apiOptions.value.filter((o) => o.value !== mapped.value)];
    emit('update:modelValue', String(mapped.value));
    emit('created', newItem);
    query.value = '';
    showToast(`${props.createLabel} created.`);
  } catch (err) {
    const errors: Record<string, string[] | undefined> =
      err instanceof ApiError && err.data && typeof err.data === 'object' ? parseErrors(err) : {};
    const msg =
      errors.name?.[0] || errors.non_field_errors?.[0] || `Failed to create ${props.createLabel.toLowerCase()}.`;
    showToast(msg, 'error');
  }
}

function onSelect(val: string) {
  if (val === CREATE_SENTINEL) {
    const name = query.value.trim();
    if (name) createItem(name);
    return;
  }
  const option = effectiveOptions.value.find((o) => o.label === val);
  emit('update:modelValue', option ? String(option.value) : '');
}

async function fetchOptions(searchText = '') {
  if (!props.loader) return;
  currentSearchText.value = searchText;
  try {
    const data = await props.loader(searchText, 1);
    apiOptions.value = data.results || [];
    currentPage.value = data.currentPage || 1;
    hasMore.value = !!data.hasMore;
  } catch {
    apiOptions.value = [];
    hasMore.value = false;
  }
}

async function fetchNextPage() {
  if (!props.loader || isLoadingMore.value || !hasMore.value) return;
  isLoadingMore.value = true;
  try {
    const data = await props.loader(currentSearchText.value, currentPage.value + 1);
    apiOptions.value = [...apiOptions.value, ...(data.results || [])];
    currentPage.value = data.currentPage || currentPage.value + 1;
    hasMore.value = !!data.hasMore;
  } catch {
    hasMore.value = false;
  } finally {
    isLoadingMore.value = false;
  }
}

function handleScroll(event: Event) {
  if (!isAsync.value) return;
  const el = event.target as HTMLElement;
  const threshold = 50;
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold) {
    fetchNextPage();
  }
}

// Native DOM input event only fires on real keystrokes, not programmatic
// value changes, so this cleanly avoids fetch loops from Reka UI's
// internal model-value syncing after selection.
function onSearchInput(event: Event) {
  if (!isAsync.value) return;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchOptions((event.target as HTMLInputElement).value), 300);
}

function onClear() {
  query.value = '';
  emit('update:modelValue', '');
  if (isAsync.value) fetchOptions();
}

watch(selectedLabel, () => {
  query.value = '';
});

onMounted(() => {
  if (isAsync.value) fetchOptions();
});
</script>

<template>
  <ComboboxRoot
    :model-value="selectedLabel"
    class="relative min-w-[200px]"
    ignore-filter
    @update:model-value="onSelect"
  >
    <ComboboxAnchor
      class="inline-flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-2.5 text-sm leading-none shadow-sm hover:bg-gray-50 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700"
    >
      <ComboboxInput
        v-model="query"
        :display-value="() => selectedLabel"
        :placeholder="placeholder"
        class="h-[34px] flex-1 bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-white dark:placeholder:text-gray-500"
        @input="onSearchInput"
      />
      <button
        v-if="modelValue"
        type="button"
        class="mr-1 cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        @click.stop="onClear"
      >
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path
            d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
          />
        </svg>
      </button>
      <ComboboxTrigger class="cursor-pointer text-gray-400">
        <svg
          class="h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </ComboboxTrigger>
    </ComboboxAnchor>

    <ComboboxContent
      class="absolute z-50 mt-1 max-h-60 w-full min-w-[200px] overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
    >
      <ComboboxViewport
        ref="viewportRef"
        class="max-h-[calc(15rem-0.5rem)] overflow-y-auto p-1"
        @scroll.passive="handleScroll"
      >
        <ComboboxEmpty v-if="!creatableOption" class="py-2 text-center text-xs text-gray-500 dark:text-gray-400">
          No results found
        </ComboboxEmpty>
        <ComboboxItem
          v-for="option in filteredOptions"
          :key="option.value"
          :value="option.label"
          class="relative flex cursor-pointer items-center rounded px-2 py-1.5 pl-7 text-sm text-gray-700 select-none data-[disabled]:pointer-events-none data-[highlighted]:bg-blue-600 data-[disabled]:text-gray-400 data-[highlighted]:text-white dark:text-gray-300 dark:data-[highlighted]:text-white"
        >
          <ComboboxItemIndicator class="absolute left-0 inline-flex w-7 items-center justify-center">
            <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                clip-rule="evenodd"
              />
            </svg>
          </ComboboxItemIndicator>
          <span>{{ option.label }}</span>
        </ComboboxItem>
        <ComboboxItem
          v-if="creatableOption"
          :value="creatableOption.value"
          class="relative flex cursor-pointer items-center rounded px-2 py-1.5 text-sm text-blue-600 select-none data-[highlighted]:bg-blue-600 data-[highlighted]:text-white dark:text-blue-400 dark:data-[highlighted]:text-white"
        >
          <svg class="mr-1.5 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              d="M10 5a.75.75 0 01.75.75v3.5h3.5a.75.75 0 010 1.5h-3.5v3.5a.75.75 0 01-1.5 0v-3.5h-3.5a.75.75 0 010-1.5h3.5v-3.5A.75.75 0 0110 5z"
            />
          </svg>
          <span>Create &ldquo;{{ creatableOption.label }}&rdquo;</span>
        </ComboboxItem>
        <div v-if="isLoadingMore" class="py-2 text-center text-xs text-gray-400 dark:text-gray-500">Loading…</div>
      </ComboboxViewport>
    </ComboboxContent>
  </ComboboxRoot>
</template>
