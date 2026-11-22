<script setup lang="ts">
import { useId } from 'vue';

withDefaults(
  defineProps<{
    label?: string;
    modelValue?: string;
    type?: string;
    errors?: string[];
    placeholder?: string;
    autocomplete?: string;
  }>(),
  {
    label: '',
    modelValue: '',
    type: 'text',
    errors: () => [],
    placeholder: '',
    autocomplete: '',
  },
);

defineEmits<{ 'update:modelValue': [value: string] }>();

const inputId = useId();
const errorsId = `${inputId}-errors`;
</script>

<template>
  <div>
    <label v-if="label" :for="inputId" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
      {{ label }}
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :aria-invalid="errors.length ? 'true' : undefined"
      :aria-describedby="errors.length ? errorsId : undefined"
      class="block w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder:text-gray-500"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <div v-if="errors.length" :id="errorsId">
      <p v-for="err in errors" :key="err" class="mt-1 text-sm text-red-600 dark:text-red-400">
        {{ err }}
      </p>
    </div>
  </div>
</template>
