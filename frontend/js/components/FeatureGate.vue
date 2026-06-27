<script setup>
import { computed, inject } from 'vue';

const props = defineProps({
  feature: { type: String, required: true },
});

const appStore = inject('appStore');
const allowed = computed(() => appStore.hasFeature(props.feature));
</script>

<template>
  <slot v-if="allowed" />
  <slot v-else name="fallback" />
</template>
