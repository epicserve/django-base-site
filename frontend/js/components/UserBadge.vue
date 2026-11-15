<script setup lang="ts">
import { computed } from 'vue';
import { userFullName, type NamedUser } from '../utils/format';
import UserAvatar from './UserAvatar.vue';

/** Any user-shaped API object, e.g. `OrgUserOut` or `MemberDetailOut`. */
type BadgeUser = NamedUser & { avatar_url?: string | null };

const props = withDefaults(
  defineProps<{
    user?: BadgeUser | null;
    size?: 'sm' | 'md' | 'rail';
    fallback?: 'initials' | 'icon';
    truncate?: boolean;
  }>(),
  { user: null, size: 'sm', fallback: 'initials', truncate: false },
);

const fullName = computed(() => userFullName(props.user));
const avatarUrl = computed(() => props.user?.avatar_url || '');
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <UserAvatar :src="avatarUrl" :name="fullName" :size="size" :fallback="fallback" />
    <span :class="truncate ? 'truncate' : ''">{{ fullName }}</span>
  </span>
</template>
