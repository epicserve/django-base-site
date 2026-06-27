<script setup>
import { computed } from 'vue';

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
});

const emit = defineEmits(['page']);

const pages = computed(() => {
  const current = props.currentPage;
  const total = props.totalPages;
  const delta = 2;
  const items = [];

  items.push(1);

  if (current - delta > 2) {
    items.push('...');
  }

  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i += 1) {
    items.push(i);
  }

  if (current + delta < total - 1) {
    items.push('...');
  }

  if (total > 1) {
    items.push(total);
  }

  return items;
});
</script>

<template>
  <nav v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-1">
    <button
      :disabled="currentPage === 1"
      class="cursor-pointer rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-300"
      @click="emit('page', currentPage - 1)"
    >
      &laquo;
    </button>

    <template v-for="(p, idx) in pages" :key="idx">
      <span v-if="p === '...'" class="px-2 py-1.5 text-sm text-gray-500 dark:text-gray-400"> &hellip; </span>
      <button
        v-else
        :class="[
          'cursor-pointer rounded-md border px-3 py-1.5 text-sm',
          p === currentPage
            ? 'border-blue-600 bg-blue-600 text-white'
            : 'border-gray-300 hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-300',
        ]"
        @click="emit('page', p)"
      >
        {{ p }}
      </button>
    </template>

    <button
      :disabled="currentPage === totalPages"
      class="cursor-pointer rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-300"
      @click="emit('page', currentPage + 1)"
    >
      &raquo;
    </button>
  </nav>
</template>
