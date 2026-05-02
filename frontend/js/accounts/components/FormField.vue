<script setup>
defineProps({
  label: { type: String, default: '' },
  modelValue: { type: String, default: '' },
  type: { type: String, default: 'text' },
  errors: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: '' },
});

defineEmits(['update:modelValue']);
</script>

<template>
  <div>
    <label
      v-if="label"
      class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
    >
      {{ label }}
    </label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      class="block w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder:text-gray-500"
      @input="$emit('update:modelValue', $event.target.value)"
    >
    <p
      v-for="err in errors"
      :key="err"
      class="mt-1 text-sm text-red-600 dark:text-red-400"
    >
      {{ err }}
    </p>
  </div>
</template>
