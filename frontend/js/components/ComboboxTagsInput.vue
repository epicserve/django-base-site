<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
  ComboboxRoot,
  ComboboxAnchor,
  ComboboxInput,
  ComboboxPortal,
  ComboboxContent,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxEmpty,
  TagsInputRoot,
  TagsInputItem,
  TagsInputItemText,
  TagsInputItemDelete,
  TagsInputInput,
} from 'reka-ui';
import { ApiError, parseErrors } from '../utils/api';
import { showToast } from '../composables/useToast';

interface TagOption {
  value: string;
  label: string;
}

/** What `create` resolves to: the new item, which becomes an option and is passed on with `created`. */
interface CreatedItem {
  id: number;
  name: string;
}

const props = withDefaults(
  defineProps<{
    options?: TagOption[];
    modelValue?: string[];
    placeholder?: string;
    tagClass?: ((value: string) => string) | null;
    /** Creates an item named after the search text; the option to create one only shows when it's set. */
    create?: (name: string) => Promise<CreatedItem>;
    createLabel?: string;
    /** The search input's `id`, for a `<label for>`. */
    inputId?: string;
    /** The `id` of the field's error message while it has one, which marks the search input invalid and describes it. */
    errorId?: string;
  }>(),
  {
    options: () => [],
    modelValue: () => [],
    placeholder: '',
    tagClass: null,
    createLabel: 'item',
  },
);

const emit = defineEmits<{ 'update:modelValue': [value: string[]]; created: [item: CreatedItem] }>();

const query = ref('');
const localOptions = ref<TagOption[]>([]);

const CREATE_SENTINEL = '__create_new__';

const mergedOptions = computed(() => [...props.options, ...localOptions.value]);

const selectedValues = computed<string[]>({
  get() {
    return props.modelValue
      .map((v) => mergedOptions.value.find((o) => String(o.value) === String(v))?.label)
      .filter((label): label is string => Boolean(label));
  },
  set(val) {
    if (val.includes(CREATE_SENTINEL)) {
      const name = query.value.trim();
      if (name) createItem(name);
      return;
    }
    const ids = val
      .map((label) => String(mergedOptions.value.find((o) => o.label === label)?.value))
      .filter((v) => v !== 'undefined');
    emit('update:modelValue', ids);
  },
});

const creatableOption = computed(() => {
  if (!props.create) return null;
  const q = query.value.trim();
  if (!q) return null;
  const lower = q.toLowerCase();
  const exactMatch = mergedOptions.value.find((o) => o.label.toLowerCase() === lower);
  if (exactMatch) return null;
  return { value: CREATE_SENTINEL, label: q };
});

const filteredOptions = computed(() => {
  const q = query.value.toLowerCase();
  return mergedOptions.value
    .filter((o) => !selectedValues.value.includes(o.label))
    .filter((o) => !q || o.label.toLowerCase().includes(q));
});

async function createItem(name: string) {
  if (!props.create) return;
  try {
    const newItem = await props.create(name);
    const mapped = { value: String(newItem.id), label: newItem.name };
    localOptions.value = [...localOptions.value, mapped];
    emit('update:modelValue', [...props.modelValue, mapped.value]);
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

function tagClassFor(label: string) {
  if (!props.tagClass) return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300';
  const opt = mergedOptions.value.find((o) => o.label === label);
  return opt ? props.tagClass(opt.value) : props.tagClass('');
}

watch(
  selectedValues,
  () => {
    query.value = '';
  },
  { deep: true },
);
</script>

<template>
  <div class="relative min-w-[200px]">
    <ComboboxRoot v-model="selectedValues" multiple ignore-filter>
      <ComboboxAnchor as-child>
        <!-- TagsInputRoot puts its `id` on the TagsInputInput below. -->
        <TagsInputRoot
          :id="inputId"
          v-model="selectedValues"
          delimiter=""
          class="flex min-h-[34px] flex-wrap items-center gap-1 rounded-md border border-gray-300 px-2 py-1 shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
        >
          <TagsInputItem
            v-for="item in selectedValues"
            :key="item"
            :value="item"
            class="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium"
            :class="tagClassFor(item)"
          >
            <TagsInputItemText />
            <TagsInputItemDelete
              class="cursor-pointer text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
            >
              <svg class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                <path
                  d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
                />
              </svg>
            </TagsInputItemDelete>
          </TagsInputItem>

          <ComboboxInput v-model="query" as-child>
            <TagsInputInput
              :placeholder="placeholder"
              :aria-invalid="errorId ? 'true' : undefined"
              :aria-describedby="errorId"
              class="min-w-[80px] flex-1 bg-transparent text-sm outline-none placeholder:text-gray-400 dark:text-white dark:placeholder:text-gray-500"
              @keydown.enter.prevent
            />
          </ComboboxInput>
        </TagsInputRoot>
      </ComboboxAnchor>

      <ComboboxPortal>
        <ComboboxContent
          class="z-50 max-h-60 w-[var(--reka-combobox-trigger-width)] overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
          position="popper"
          :side-offset="4"
        >
          <ComboboxEmpty v-if="!creatableOption" class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
            No results found
          </ComboboxEmpty>
          <ComboboxItem
            v-for="option in filteredOptions"
            :key="option.value"
            :value="option.label"
            class="flex cursor-pointer items-center justify-between px-3 py-1.5 text-sm hover:bg-blue-600 hover:text-white data-[highlighted]:bg-blue-600 data-[highlighted]:text-white dark:text-gray-300 dark:hover:text-white"
          >
            {{ option.label }}
            <ComboboxItemIndicator>
              <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                  clip-rule="evenodd"
                />
              </svg>
            </ComboboxItemIndicator>
          </ComboboxItem>
          <ComboboxItem
            v-if="creatableOption"
            :value="creatableOption.value"
            class="flex cursor-pointer items-center px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-600 hover:text-white data-[highlighted]:bg-blue-600 data-[highlighted]:text-white dark:text-blue-400 dark:hover:text-white"
          >
            <svg class="mr-1.5 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                d="M10 5a.75.75 0 01.75.75v3.5h3.5a.75.75 0 010 1.5h-3.5v3.5a.75.75 0 01-1.5 0v-3.5h-3.5a.75.75 0 010-1.5h3.5v-3.5A.75.75 0 0110 5z"
              />
            </svg>
            Create &ldquo;{{ creatableOption.label }}&rdquo;
          </ComboboxItem>
        </ComboboxContent>
      </ComboboxPortal>
    </ComboboxRoot>
  </div>
</template>
