<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/outline';

withDefaults(defineProps<{ modelValue?: string; placeholder?: string }>(), {
  modelValue: '',
  placeholder: 'Search...',
});

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value);
}

function clear() {
  emit('update:modelValue', '');
}
</script>

<template>
  <div class="relative">
    <input
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      class="rounded-md border border-gray-300 py-1.5 pl-2.5 pr-8 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
      @input="onInput"
    />
    <button
      v-if="modelValue"
      type="button"
      aria-label="Clear Search"
      class="absolute inset-y-0 right-0 flex items-center pr-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
      @click="clear"
    >
      <XMarkIcon class="h-4 w-4" />
    </button>
  </div>
</template>
