<script setup>
import { computed, ref, watch } from 'vue';
import { UserIcon } from '@heroicons/vue/24/solid';

const props = defineProps({
  src: { type: String, default: '' },
  name: { type: String, default: '' },
  size: { type: String, default: 'sm', validator: (v) => ['sm', 'md', 'rail'].includes(v) },
  fallback: { type: String, default: 'initials', validator: (v) => ['initials', 'icon'].includes(v) },
});

const sizes = {
  sm: 'h-5 w-5 text-[10px]',
  md: 'h-6 w-6 text-xs',
  rail: 'h-7 w-7 text-xs',
};

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-3.5 w-3.5',
  rail: 'h-4 w-4',
};

const imgFailed = ref(false);
watch(() => props.src, () => { imgFailed.value = false; });
const showImg = computed(() => !!props.src && !imgFailed.value);

const initials = computed(() => {
  const parts = (props.name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
});

const initialsBg = computed(() => {
  const s = (props.name || '').trim().toLowerCase();
  if (!s) return '';
  let h = 0;
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  const hue = Math.abs(h) % 360;
  return `hsl(${hue}, 45%, 42%)`;
});
</script>

<template>
  <img
    v-if="showImg"
    :src="src"
    alt=""
    class="inline-block shrink-0 aspect-square rounded-full object-cover"
    :class="sizes[size]"
    @error="imgFailed = true"
  >
  <span
    v-else-if="fallback === 'icon'"
    class="inline-flex shrink-0 aspect-square items-center justify-center rounded-full bg-gray-200 font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-400"
    :class="sizes[size]"
    :aria-label="name"
  >
    <UserIcon :class="iconSizes[size]" />
  </span>
  <span
    v-else
    class="inline-flex shrink-0 aspect-square items-center justify-center rounded-full font-medium text-white"
    :class="sizes[size]"
    :style="{ backgroundColor: initialsBg }"
    :aria-label="name"
  >
    {{ initials }}
  </span>
</template>
