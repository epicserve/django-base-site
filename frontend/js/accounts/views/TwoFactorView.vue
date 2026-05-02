<script setup>
import { ref, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';
import { safeNextUrl } from '../../utils/redirect';

const route = useRoute();
const router = useRouter();
const appStore = inject('appStore');

const code = ref('');
const errors = ref({});
const loading = ref(false);

function getRedirectUrl() {
  return safeNextUrl(route.query.next);
}

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    const data = await authApi.submit2FA(code.value);

    appStore.setUser(data.data?.user || null);
    await appStore.fetchContext();
    window.location.href = getRedirectUrl();
  } catch (err) {
    if (err.response?.status === 409) {
      window.location.href = getRedirectUrl();
      return;
    }
    if (err.response?.status === 410) {
      // Flow expired — back to login
      router.push({ name: 'login' });
      return;
    }
    errors.value = err.data ? parseAllauthErrors(err.data) : {
      non_field_errors: ['Invalid code.'],
    };
    loading.value = false;
  }
}
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
      Two-factor authentication
    </h1>
    <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
      Enter the 6-digit code from your authenticator app, or one of your recovery codes.
    </p>
    <form
      class="mt-6 space-y-4"
      @submit.prevent="onSubmit"
    >
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField
        v-model="code"
        label="Code"
        autocomplete="one-time-code"
        inputmode="numeric"
        :errors="errors.code || []"
      />
      <button
        type="submit"
        :disabled="loading || !code"
        class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Verifying…' : 'Continue' }}
      </button>
    </form>
  </AuthLayout>
</template>
