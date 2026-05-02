<script setup>
const props = defineProps({
  modelValue: { type: Boolean, required: true },
  label: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue']);

function toggle() {
  emit('update:modelValue', !props.modelValue);
}
</script>

<template>
  <div class="flex items-center gap-3">
    <button
      :class="[
        'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full',
        'border-2 border-transparent transition-colors',
        modelValue ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600',
      ]"
      role="switch"
      :aria-checked="modelValue"
      type="button"
      @click="toggle"
    >
      <span
        :class="[
          'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow ring-0 transition-transform',
          modelValue ? 'translate-x-4' : 'translate-x-0',
        ]"
      />
    </button>
    <span
      v-if="label"
      class="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 select-none"
      @click="toggle"
    >
      {{ label }}
    </span>
  </div>
</template>
