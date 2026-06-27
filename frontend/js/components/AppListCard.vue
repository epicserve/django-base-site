<script setup>
import { useSlots } from 'vue';

const slots = useSlots();
</script>

<template>
  <div class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
    <div v-if="slots.filters" class="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
      <slot name="filters" />
    </div>
    <div class="overflow-x-auto">
      <slot />
    </div>
    <div v-if="slots.pagination" class="border-t border-gray-200 px-4 pb-3 dark:border-gray-700">
      <slot name="pagination" />
    </div>
  </div>
</template>
