import { ref } from 'vue';

export type ToastType = 'success' | 'error';

/** What `AppToast` registers with `setToastRef()` while it's mounted. */
export interface ToastHost {
  addToast(message: string, type?: ToastType, duration?: number): void;
}

const toastRef = ref<ToastHost | null>(null);

export function setToastRef(instance: ToastHost | null) {
  toastRef.value = instance;
}

export function showToast(message: string, type: ToastType = 'success', duration = 4000) {
  if (toastRef.value) {
    toastRef.value.addToast(message, type, duration);
  }
}
