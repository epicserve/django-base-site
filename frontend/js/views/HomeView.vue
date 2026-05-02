<script setup>
import { inject } from 'vue';

const appStore = inject('appStore');
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
      Welcome{{ appStore.user?.first_name ? `, ${appStore.user.first_name}` : '' }}!
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      You're signed in to {{ appStore.siteName }}. Use the menus above to manage your account
      <span v-if="appStore.org">and the {{ appStore.org.name }} organization</span>.
    </p>
  </div>
</template>
