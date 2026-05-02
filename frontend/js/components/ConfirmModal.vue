<script setup>
import { ref } from 'vue';
import AppModal from './AppModal.vue';

const isOpen = ref(false);
const title = ref('Confirm');
const message = ref('');
let resolveFn = null;

function confirm(msg, ttl = 'Confirm') {
  message.value = msg;
  title.value = ttl;
  isOpen.value = true;
  return new Promise((resolve) => {
    resolveFn = resolve;
  });
}

function onConfirm() {
  isOpen.value = false;
  if (resolveFn) resolveFn(true);
  resolveFn = null;
}

function onClose() {
  isOpen.value = false;
  if (resolveFn) resolveFn(false);
  resolveFn = null;
}

defineExpose({ confirm });
</script>

<template>
  <AppModal
    :open="isOpen"
    :title="title"
    @close="onClose"
  >
    <p class="text-gray-700 dark:text-gray-300">
      {{ message }}
    </p>
    <template #footer>
      <button
        class="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 dark:hover:text-white"
        @click="onClose"
      >
        Cancel
      </button>
      <button
        class="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
        @click="onConfirm"
      >
        OK
      </button>
    </template>
  </AppModal>
</template>
