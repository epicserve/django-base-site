<script setup>
import { ref, onMounted } from 'vue';
import { SwatchIcon } from '@heroicons/vue/24/outline';

const currentTheme = ref('auto');

function setTheme(theme) {
  currentTheme.value = theme;
  localStorage.setItem('theme', theme);
  if (theme === 'auto') {
    const resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', resolved);
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
}

onMounted(() => {
  currentTheme.value = localStorage.getItem('theme') || 'auto';
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme.value === 'auto') {
      setTheme('auto');
    }
  });
});
</script>

<!-- eslint-disable max-len -->
<template>
  <div class="flex items-center justify-between px-4 py-2">
    <span class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
      <SwatchIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
      Theme
    </span>
    <div class="inline-flex rounded-full border border-gray-200 dark:border-gray-600">
      <button
        type="button"
        class="cursor-pointer rounded-l-full p-1.5 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
        :class="{ 'bg-gray-200 dark:bg-gray-600': currentTheme === 'light' }"
        aria-label="Light theme"
        :aria-pressed="currentTheme === 'light'"
        @click="setTheme('light')"
      >
        <svg
          class="h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M12 2.25a.75.75 0 0 1 .75.75v2.25a.75.75 0 0 1-1.5 0V3a.75.75 0 0 1 .75-.75ZM7.5 12a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0ZM18.894 6.166a.75.75 0 0 0-1.06-1.06l-1.591 1.59a.75.75 0 1 0 1.06 1.061l1.591-1.59ZM21.75 12a.75.75 0 0 1-.75.75h-2.25a.75.75 0 0 1 0-1.5H21a.75.75 0 0 1 .75.75ZM17.834 18.894a.75.75 0 0 0 1.06-1.06l-1.59-1.591a.75.75 0 1 0-1.061 1.06l1.59 1.591ZM12 18a.75.75 0 0 1 .75.75V21a.75.75 0 0 1-1.5 0v-2.25A.75.75 0 0 1 12 18ZM7.758 17.303a.75.75 0 0 0-1.061-1.06l-1.591 1.59a.75.75 0 0 0 1.06 1.061l1.591-1.59ZM6 12a.75.75 0 0 1-.75.75H3a.75.75 0 0 1 0-1.5h2.25A.75.75 0 0 1 6 12ZM6.697 7.757a.75.75 0 0 0 1.06-1.06l-1.59-1.591a.75.75 0 0 0-1.061 1.06l1.59 1.591Z" />
        </svg>
      </button>
      <button
        type="button"
        class="cursor-pointer border-x border-gray-200 p-1.5 text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        :class="{ 'bg-gray-200 dark:bg-gray-600': currentTheme === 'dark' }"
        aria-label="Dark theme"
        :aria-pressed="currentTheme === 'dark'"
        @click="setTheme('dark')"
      >
        <svg
          class="h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M9.528 1.718a.75.75 0 0 1 .162.819A8.97 8.97 0 0 0 9 6a9 9 0 0 0 9 9 8.97 8.97 0 0 0 3.463-.69.75.75 0 0 1 .981.98 10.503 10.503 0 0 1-9.694 6.46c-5.799 0-10.5-4.7-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 0 1 .818.162Z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
      <button
        type="button"
        class="cursor-pointer rounded-r-full p-1.5 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
        :class="{ 'bg-gray-200 dark:bg-gray-600': currentTheme === 'auto' }"
        aria-label="Auto theme"
        :aria-pressed="currentTheme === 'auto'"
        @click="setTheme('auto')"
      >
        <svg
          class="h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0V12a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 12V5.25"
          />
        </svg>
      </button>
    </div>
  </div>
</template>
