<script setup>
import { computed } from 'vue';
import { userFullName } from '../utils/format';
import UserAvatar from './UserAvatar.vue';

const props = defineProps({
  user: { type: Object, default: null },
  size: { type: String, default: 'sm' },
  fallback: { type: String, default: 'initials' },
  truncate: { type: Boolean, default: false },
});

const fullName = computed(() => userFullName(props.user || {}));
const avatarUrl = computed(() => props.user?.avatar_url || '');
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <UserAvatar
      :src="avatarUrl"
      :name="fullName"
      :size="size"
      :fallback="fallback"
    />
    <span :class="truncate ? 'truncate' : ''">{{ fullName }}</span>
  </span>
</template>
