<template>
  <div class="flex min-h-[60vh] items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div
        class="rounded-xl border border-gray-200 bg-white px-8 py-10 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      >
        <slot />
      </div>
      <slot name="footer" />
    </div>
  </div>
</template>
