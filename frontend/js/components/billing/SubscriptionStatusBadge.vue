<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: { type: String, default: null },
});

const BLUE = 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-900/30 dark:text-blue-300';
const GREEN = 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-900/30 dark:text-green-300';
const RED = 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-900/30 dark:text-red-300';
const GRAY = 'bg-gray-100 text-gray-700 ring-gray-500/20 dark:bg-gray-700 dark:text-gray-300';
const AMBER = 'bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-900/30 dark:text-amber-300';

const STYLE = {
  trialing: { label: 'Trial', class: BLUE },
  active: { label: 'Active', class: GREEN },
  past_due: { label: 'Past due', class: RED },
  canceled: { label: 'Canceled', class: GRAY },
  incomplete: { label: 'Pending', class: AMBER },
  incomplete_expired: { label: 'Expired', class: GRAY },
  unpaid: { label: 'Unpaid', class: RED },
  paused: { label: 'Paused', class: GRAY },
};

const style = computed(() => STYLE[props.status] || null);
</script>

<template>
  <span
    v-if="style"
    class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset"
    :class="style.class"
  >
    {{ style.label }}
  </span>
</template>
