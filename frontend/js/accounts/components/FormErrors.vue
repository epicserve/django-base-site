<script setup lang="ts">
withDefaults(defineProps<{ errors?: string[] }>(), {
  errors: () => [],
});
</script>

<template>
  <div v-if="errors.length" class="rounded-lg bg-red-50 px-4 py-3 dark:bg-red-900/20">
    <p v-for="error in errors" :key="error" class="text-sm text-red-600 dark:text-red-400">
      {{ error }}
    </p>
  </div>
</template>
