<script setup>
import {
  ref, computed, watch, onMounted,
} from 'vue';
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
import { get, post } from '../utils/api';
import { showToast } from '../composables/useToast';

const props = defineProps({
  options: { type: Array, default: () => [] },
  prependOptions: { type: Array, default: () => [] },
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  url: { type: String, default: '' },
  // Async loader for sources that can't be expressed as a single URL (e.g. a
  // combined users + teams dropdown). Receives `(q, page)` and resolves to
  // `{ results: [{ value, label }], hasMore: bool, currentPage: int }`. Takes
  // precedence over `url` when provided.
  loader: { type: Function, default: null },
  valueField: { type: String, default: 'id' },
  labelField: { type: [String, Function], default: 'name' },
  initialDisplayValue: { type: String, default: '' },
  createUrl: { type: String, default: '' },
  createLabel: { type: String, default: 'item' },
});

const emit = defineEmits(['update:modelValue', 'created']);

const query = ref('');
const apiOptions = ref([]);
const currentPage = ref(1);
const hasMore = ref(false);
const isLoadingMore = ref(false);
const currentSearchText = ref('');
const viewportRef = ref(null);
let debounceTimer = null;

function mapResult(item) {
  const label = typeof props.labelField === 'function'
    ? props.labelField(item)
    : item[props.labelField];
  return { value: String(item[props.valueField]), label: label || '' };
}

const isAsync = computed(() => props.loader || !!props.url);

const effectiveOptions = computed(() => {
  const base = isAsync.value ? apiOptions.value : props.options;
  return props.prependOptions.length ? [...props.prependOptions, ...base] : base;
});

const selectedLabel = computed(() => {
  if (!props.modelValue) return '';
  const match = effectiveOptions.value
    .find((o) => String(o.value) === String(props.modelValue));
  return match?.label || props.initialDisplayValue || '';
});

const CREATE_SENTINEL = '__create_new__';

const creatableOption = computed(() => {
  if (!props.createUrl) return null;
  const q = query.value.trim();
  if (!q) return null;
  const lower = q.toLowerCase();
  const exactMatch = effectiveOptions.value.find((o) => o.label.toLowerCase() === lower);
  if (exactMatch) return null;
  return { value: CREATE_SENTINEL, label: q };
});

const filteredOptions = computed(() => effectiveOptions.value);

async function createItem(name) {
  try {
    const newItem = await post(props.createUrl, { name });
    const mapped = mapResult(newItem);
    apiOptions.value = [mapped, ...apiOptions.value.filter((o) => o.value !== mapped.value)];
    emit('update:modelValue', String(mapped.value));
    emit('created', newItem);
    query.value = '';
    showToast(`${props.createLabel} created.`);
  } catch (err) {
    const msg = err?.data?.name?.[0]
      || err?.data?.non_field_errors?.[0]
      || `Failed to create ${props.createLabel.toLowerCase()}.`;
    showToast(msg, 'error');
  }
}

function onSelect(val) {
  if (val === CREATE_SENTINEL) {
    const name = query.value.trim();
    if (name) createItem(name);
    return;
  }
  const option = effectiveOptions.value.find((o) => o.label === val);
  emit('update:modelValue', option ? String(option.value) : '');
}

async function fetchOptions(searchText = '') {
  if (!isAsync.value) return;
  currentSearchText.value = searchText;
  try {
    if (props.loader) {
      const data = await props.loader(searchText, 1);
      apiOptions.value = data.results || [];
      currentPage.value = data.currentPage || 1;
      hasMore.value = !!data.hasMore;
      return;
    }
    const params = { page_size: 30, page: 1 };
    if (searchText) params.q = searchText;
    const data = await get(props.url, params);
    const results = data.results || data;
    apiOptions.value = results.map(mapResult);
    currentPage.value = data.current_page_num || 1;
    hasMore.value = !!data.next;
  } catch {
    apiOptions.value = [];
    hasMore.value = false;
  }
}

async function fetchNextPage() {
  if (!isAsync.value || isLoadingMore.value || !hasMore.value) return;
  isLoadingMore.value = true;
  try {
    if (props.loader) {
      const data = await props.loader(currentSearchText.value, currentPage.value + 1);
      apiOptions.value = [...apiOptions.value, ...(data.results || [])];
      currentPage.value = data.currentPage || currentPage.value + 1;
      hasMore.value = !!data.hasMore;
      return;
    }
    const params = { page_size: 30, page: currentPage.value + 1 };
    if (currentSearchText.value) params.q = currentSearchText.value;
    const data = await get(props.url, params);
    const results = data.results || data;
    apiOptions.value = [...apiOptions.value, ...results.map(mapResult)];
    currentPage.value = data.current_page_num || currentPage.value + 1;
    hasMore.value = !!data.next;
  } catch {
    hasMore.value = false;
  } finally {
    isLoadingMore.value = false;
  }
}

function handleScroll(event) {
  if (!isAsync.value) return;
  const el = event.target;
  const threshold = 50;
  if (el.scrollHeight - el.scrollTop - el.clientHeight < threshold) {
    fetchNextPage();
  }
}

// Native DOM input event only fires on real keystrokes, not programmatic
// value changes, so this cleanly avoids fetch loops from Reka UI's
// internal model-value syncing after selection.
function onSearchInput(event) {
  if (!isAsync.value) return;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => fetchOptions(event.target.value), 300);
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
    <ComboboxAnchor class="inline-flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-2.5 text-sm leading-none shadow-sm hover:bg-gray-50 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700">
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
        <svg
          class="h-4 w-4"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <!-- eslint-disable-next-line max-len -->
          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
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

    <ComboboxContent class="absolute z-50 mt-1 max-h-60 w-full min-w-[200px] overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
      <ComboboxViewport
        ref="viewportRef"
        class="max-h-[calc(15rem-0.5rem)] overflow-y-auto p-1"
        @scroll.passive="handleScroll"
      >
        <ComboboxEmpty
          v-if="!creatableOption"
          class="py-2 text-center text-xs text-gray-500 dark:text-gray-400"
        >
          No results found
        </ComboboxEmpty>
        <ComboboxItem
          v-for="option in filteredOptions"
          :key="option.value"
          :value="option.label"
          class="relative flex cursor-pointer items-center rounded px-2 py-1.5 pl-7 text-sm text-gray-700 select-none data-[disabled]:pointer-events-none data-[highlighted]:bg-blue-600 data-[disabled]:text-gray-400 data-[highlighted]:text-white dark:text-gray-300 dark:data-[highlighted]:text-white"
        >
          <ComboboxItemIndicator class="absolute left-0 inline-flex w-7 items-center justify-center">
            <svg
              class="h-4 w-4"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <!-- eslint-disable max-len -->
              <path
                fill-rule="evenodd"
                d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                clip-rule="evenodd"
              />
              <!-- eslint-enable max-len -->
            </svg>
          </ComboboxItemIndicator>
          <span>{{ option.label }}</span>
        </ComboboxItem>
        <ComboboxItem
          v-if="creatableOption"
          :value="creatableOption.value"
          class="relative flex cursor-pointer items-center rounded px-2 py-1.5 text-sm text-blue-600 select-none data-[highlighted]:bg-blue-600 data-[highlighted]:text-white dark:text-blue-400 dark:data-[highlighted]:text-white"
        >
          <svg
            class="mr-1.5 h-4 w-4"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <!-- eslint-disable-next-line max-len -->
            <path d="M10 5a.75.75 0 01.75.75v3.5h3.5a.75.75 0 010 1.5h-3.5v3.5a.75.75 0 01-1.5 0v-3.5h-3.5a.75.75 0 010-1.5h3.5v-3.5A.75.75 0 0110 5z" />
          </svg>
          <span>Create &ldquo;{{ creatableOption.label }}&rdquo;</span>
        </ComboboxItem>
        <div
          v-if="isLoadingMore"
          class="py-2 text-center text-xs text-gray-400 dark:text-gray-500"
        >
          Loading…
        </div>
      </ComboboxViewport>
    </ComboboxContent>
  </ComboboxRoot>
</template>
