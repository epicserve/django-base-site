<script setup>
import ManageTeamsApp from '@/apps/ManageTeamsApp.vue';
</script>

<template>
  <ManageTeamsApp team-list-url="/api/teams/" organization-member-list-url="/api/organization-members/" />
</template>
