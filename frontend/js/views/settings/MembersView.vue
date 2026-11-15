<script setup lang="ts">
import ManageOrganizationApp from '@/apps/ManageOrganizationApp.vue';
import { useAppStore } from '@/stores/app';

const appStore = useAppStore();
</script>

<template>
  <ManageOrganizationApp
    v-if="appStore.org && appStore.user"
    :org-name="appStore.org.name"
    :current-user-id="appStore.user.id"
  />
</template>
