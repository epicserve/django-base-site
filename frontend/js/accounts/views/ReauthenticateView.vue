<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AuthLayout from '@/layouts/AuthLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';

const route = useRoute();
const router = useRouter();

const password = ref('');
const errors = ref({});
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    await authApi.reauthenticate(password.value);
    const next = route.query.next || '/accounts/security/';

    router.push(next);
  } catch (err) {
    errors.value = err.data ? parseAllauthErrors(err.data) : {
      non_field_errors: ['Could not verify password.'],
    };
    loading.value = false;
  }
}
</script>

<template>
  <AuthLayout>
    <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
      Confirm your password
    </h1>
    <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
      For your security, please re-enter your password to continue.
    </p>
    <form
      class="mt-6 space-y-4"
      @submit.prevent="onSubmit"
    >
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField
        v-model="password"
        type="password"
        label="Password"
        autocomplete="current-password"
        :errors="errors.password || []"
      />
      <button
        type="submit"
        :disabled="loading || !password"
        class="w-full cursor-pointer rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Verifying…' : 'Continue' }}
      </button>
    </form>
  </AuthLayout>
</template>
