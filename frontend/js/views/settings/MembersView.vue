<script setup>
import { inject } from 'vue';
import ManageOrganizationApp from '@/apps/ManageOrganizationApp.vue';

const appStore = inject('appStore');
</script>

<template>
  <ManageOrganizationApp
    v-if="appStore.org"
    :org-name="appStore.org.name"
    organization-member-list-url="/api/organization-members/"
    organization-invite-list-url="/api/organization-invites/"
    :current-user-id="appStore.user.id"
  />
</template>
