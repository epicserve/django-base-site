<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '@/stores/app';

const props = defineProps<{ feature: string }>();

const appStore = useAppStore();
const allowed = computed(() => appStore.hasFeature(props.feature));
</script>

<template>
  <slot v-if="allowed" />
  <slot v-else name="fallback" />
</template>
