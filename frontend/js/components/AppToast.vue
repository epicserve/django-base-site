<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import {
  ToastProvider,
  ToastRoot,
  ToastTitle,
  ToastViewport,
} from 'reka-ui';

const toasts = ref([]);
let nextId = 0;

function addToast(message, type = 'success', duration = 4000) {
  const id = nextId;
  nextId += 1;
  toasts.value.push({
    id,
    message,
    type,
    duration,
    open: true,
  });
}

function closeToast(id) {
  const toast = toasts.value.find((t) => t.id === id);
  if (toast) toast.open = false;
}

function removeToast(id) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

onMounted(() => {
  window.__addToast = addToast;
});

onUnmounted(() => {
  delete window.__addToast;
});

defineExpose({ addToast });
</script>

<template>
  <ToastProvider
    :duration="4000"
    swipe-direction="right"
  >
    <ToastRoot
      v-for="toast in toasts"
      :key="toast.id"
      v-model:open="toast.open"
      :duration="toast.duration"
      class="toast-root group pointer-events-auto flex items-start gap-3 rounded-lg border bg-white px-4 py-3 text-sm shadow-lg ring-1 ring-black/5 dark:bg-gray-800 dark:ring-white/10"
      :class="toast.type === 'error'
        ? 'border-red-200 dark:border-red-900/50'
        : 'border-gray-200 dark:border-gray-700'"
      @animationend="(e) => { if (!toast.open && e.animationName.includes('slide-out')) removeToast(toast.id) }"
    >
      <svg
        v-if="toast.type === 'error'"
        class="mt-0.5 h-5 w-5 shrink-0 text-red-500"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          :d="'M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0'
            + ' 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0'
            + ' 00-1.06-1.06L10 8.94 8.28 7.22z'"
          clip-rule="evenodd"
        />
      </svg>
      <svg
        v-else
        class="mt-0.5 h-5 w-5 shrink-0 text-green-500"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          :d="'M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483'
            + ' 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z'"
          clip-rule="evenodd"
        />
      </svg>
      <ToastTitle class="flex-1 pt-0.5 font-medium text-gray-900 dark:text-gray-100">
        {{ toast.message }}
      </ToastTitle>
      <button
        class="cursor-pointer shrink-0 rounded p-0.5 text-gray-400 opacity-0 transition hover:text-gray-600 group-hover:opacity-100 dark:hover:text-gray-200"
        @click="closeToast(toast.id)"
      >
        <!-- eslint-disable max-len -->
        <svg
          class="h-4 w-4"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
        </svg>
        <!-- eslint-enable max-len -->
      </button>
    </ToastRoot>

    <ToastViewport class="fixed bottom-4 right-4 z-50 flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2 outline-none" />
  </ToastProvider>
</template>

<style>
@keyframes toast-slide-in {
  from {
    transform: translateY(100%) scale(0.9);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

@keyframes toast-slide-out {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(100%) scale(0.9);
    opacity: 0;
  }
}

@keyframes toast-swipe-out {
  from {
    transform: translateX(var(--reka-toast-swipe-end-x));
  }
  to {
    transform: translateX(calc(100% + 1rem));
  }
}

.toast-root {
  transition: transform 200ms ease-out;
}

.toast-root[data-state='open'] {
  animation: toast-slide-in 400ms cubic-bezier(0.21, 1.02, 0.73, 1);
}

.toast-root[data-state='closed'] {
  animation: toast-slide-out 200ms cubic-bezier(0.06, 0.71, 0.55, 1);
}

.toast-root[data-swipe='move'] {
  transform: translateX(var(--reka-toast-swipe-move-x));
  transition: none;
}

.toast-root[data-swipe='cancel'] {
  transform: translateX(0);
}

.toast-root[data-swipe='end'] {
  animation: toast-swipe-out 150ms ease-out;
}
</style>
