<script setup>
defineProps({
  modelValue: { type: String, required: true },
  annualSavingsLabel: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue']);

function setCycle(value) {
  emit('update:modelValue', value);
}
</script>

<template>
  <div class="inline-flex rounded-full bg-gray-100 p-1 dark:bg-gray-800">
    <button
      type="button"
      class="cursor-pointer rounded-full px-4 py-1.5 text-sm transition"
      :class="
        modelValue === 'monthly'
          ? 'bg-white shadow text-gray-900 dark:bg-gray-700 dark:text-white'
          : 'text-gray-500 dark:text-gray-400'
      "
      :aria-pressed="modelValue === 'monthly'"
      @click="setCycle('monthly')"
    >
      Monthly
    </button>
    <button
      type="button"
      class="cursor-pointer rounded-full px-4 py-1.5 text-sm transition"
      :class="
        modelValue === 'annual'
          ? 'bg-white shadow text-gray-900 dark:bg-gray-700 dark:text-white'
          : 'text-gray-500 dark:text-gray-400'
      "
      :aria-pressed="modelValue === 'annual'"
      @click="setCycle('annual')"
    >
      Annual
      <span v-if="annualSavingsLabel" class="ml-1 text-xs text-green-600 dark:text-green-400">
        {{ annualSavingsLabel }}
      </span>
    </button>
  </div>
</template>
