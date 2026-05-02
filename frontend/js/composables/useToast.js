import { ref } from 'vue';

const toastRef = ref(null);

export function setToastRef(instance) {
  toastRef.value = instance;
}

export function showToast(message, type = 'success', duration = 4000) {
  if (toastRef.value) {
    toastRef.value.addToast(message, type, duration);
  } else if (window.__addToast) {
    window.__addToast(message, type, duration);
  }
}
