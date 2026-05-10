import { computed, inject } from 'vue';

export function useFeature(key) {
  const appStore = inject('appStore');
  return {
    enabled: computed(() => appStore.hasFeature(key)),
    value: computed(() => appStore.featureValue(key)),
  };
}
