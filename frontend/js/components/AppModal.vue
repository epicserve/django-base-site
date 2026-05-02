<script setup>
import {
  DialogRoot,
  DialogPortal,
  DialogOverlay,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogClose,
  VisuallyHidden,
} from 'reka-ui';

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: '' },
});

const emit = defineEmits(['close', 'openAutoFocus']);

function onOpenChange(val) {
  if (!val) emit('close');
}

function onOpenAutoFocus(event) {
  emit('openAutoFocus', event);
}
</script>

<template>
  <DialogRoot
    :open="props.open"
    @update:open="onOpenChange"
  >
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-40 bg-black/50" />
      <DialogContent
        :class="[
          'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
          'w-full rounded-lg bg-white dark:bg-gray-800 shadow-xl',
          'max-h-[85vh] flex flex-col',
          size === 'xl' ? 'max-w-4xl' : size === 'lg' ? 'max-w-2xl' : 'max-w-md',
        ]"
        @open-auto-focus="onOpenAutoFocus"
      >
        <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <DialogTitle class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ title }}
          </DialogTitle>
          <VisuallyHidden as-child>
            <DialogDescription />
          </VisuallyHidden>
          <DialogClose
            class="cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <!-- eslint-disable max-len -->
            <svg
              class="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
            <!-- eslint-enable max-len -->
          </DialogClose>
        </div>
        <div class="px-6 py-4 min-h-0 overflow-y-auto">
          <slot />
        </div>
        <div
          v-if="$slots.footer"
          class="flex justify-end gap-2 border-t border-gray-200 dark:border-gray-700 px-6 py-4"
        >
          <slot name="footer" />
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
