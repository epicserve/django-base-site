<script setup>
import { RouterLink, useRoute } from 'vue-router';

const route = useRoute();

const tabs = [
  { to: { name: 'account-general' }, label: 'General', activeNames: ['account-general'] },
  { to: { name: 'account-email' }, label: 'Email Addresses', activeNames: ['account-email'] },
  { to: { name: 'account-password-change' }, label: 'Change Password', activeNames: ['account-password-change'] },
  {
    to: { name: 'account-security' },
    label: 'Security',
    activeNames: ['account-security', 'account-totp', 'account-recovery-codes', 'account-passkeys'],
  },
];
</script>

<template>
  <div class="mx-auto max-w-2xl w-full">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
      Account Settings
    </h1>
    <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
      <nav class="flex gap-4 -mb-px">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.label"
          :to="tab.to"
          :class="[
            'inline-block cursor-pointer pb-3 text-sm font-medium border-b-2',
            tab.activeNames.includes(route.name)
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : [
                'border-transparent text-gray-500',
                'hover:text-gray-700 hover:border-gray-300',
                'dark:text-gray-400 dark:hover:text-gray-300',
              ].join(' '),
          ]"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>
    </div>
    <slot />
  </div>
</template>
