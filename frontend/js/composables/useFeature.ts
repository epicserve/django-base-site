import { computed } from 'vue';
import { useAppStore } from '@/stores/app';

export function useFeature(key: string) {
  const appStore = useAppStore();
  return {
    enabled: computed(() => appStore.hasFeature(key)),
    value: computed(() => appStore.featureValue(key)),
  };
}
