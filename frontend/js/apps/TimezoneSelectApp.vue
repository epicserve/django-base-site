<script setup>
import { ref, computed } from 'vue';
import TIMEZONE_CHOICES, { getTimezoneLabel } from '../utils/timezones';

const props = defineProps({
  currentTimezone: { type: String, required: true },
  fieldName: { type: String, default: 'timezone' },
  modelValue: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue']);

const search = ref('');
const isOpen = ref(false);
const selected = ref(props.currentTimezone);

const selectedLabel = computed(() => getTimezoneLabel(selected.value));

const grouped = computed(() => {
  const q = search.value.toLowerCase();
  const matches = q
    ? TIMEZONE_CHOICES.filter(
      (tz) => tz.label.toLowerCase().includes(q)
          || tz.value.toLowerCase().includes(q)
          || tz.region.toLowerCase().includes(q),
    )
    : TIMEZONE_CHOICES;

  return matches.reduce((groups, tz) => {
    if (!groups[tz.region]) groups[tz.region] = [];
    groups[tz.region].push(tz);
    return groups;
  }, {});
});

const hasResults = computed(() => Object.keys(grouped.value).length > 0);

function select(tz) {
  selected.value = tz.value;
  emit('update:modelValue', tz.value);
  search.value = '';
  isOpen.value = false;
}

function onBlur() {
  setTimeout(() => {
    isOpen.value = false;
    search.value = '';
  }, 200);
}
</script>

<template>
  <div class="relative">
    <input
      :name="fieldName"
      type="hidden"
      :value="selected"
    >
    <input
      type="text"
      :value="isOpen ? search : selectedLabel"
      :placeholder="selectedLabel || 'Search timezones...'"
      class="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white sm:text-sm"
      autocomplete="off"
      @focus="isOpen = true; search = ''"
      @blur="onBlur"
      @input="search = $event.target.value; isOpen = true"
    >
    <ul
      v-if="isOpen && hasResults"
      class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 dark:bg-gray-800 dark:ring-gray-600"
    >
      <template
        v-for="(tzList, region) in grouped"
        :key="region"
      >
        <li class="sticky top-0 bg-gray-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:bg-gray-700 dark:text-gray-400">
          {{ region }}
        </li>
        <li
          v-for="tz in tzList"
          :key="tz.value"
          class="cursor-pointer select-none px-3 py-2 text-sm hover:bg-blue-50 dark:hover:bg-gray-700"
          :class="{ 'bg-blue-50 dark:bg-gray-700 font-medium': tz.value === selected }"
          @mousedown.prevent="select(tz)"
        >
          {{ tz.label }}
        </li>
      </template>
    </ul>
    <p
      v-if="isOpen && !hasResults"
      class="absolute z-10 mt-1 w-full rounded-md bg-white px-3 py-2 text-sm text-gray-500 shadow-lg ring-1 ring-black/5 dark:bg-gray-800 dark:ring-gray-600 dark:text-gray-400"
    >
      No timezones match "{{ search }}"
    </p>
  </div>
</template>
