<script setup>
import { ref } from 'vue';
import AccountLayout from '@/layouts/AccountLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import { authApi, parseAllauthErrors } from '../api';
import { showToast } from '../../composables/useToast';

const oldPassword = ref('');
const newPassword1 = ref('');
const newPassword2 = ref('');
const errors = ref({});
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    await authApi.changePassword({
      current_password: oldPassword.value,
      new_password: newPassword1.value,
    });
    showToast('Your password has been changed.');
    oldPassword.value = '';
    newPassword1.value = '';
    newPassword2.value = '';
  } catch (err) {
    if (err.data) {
      errors.value = parseAllauthErrors(err.data);
    } else {
      errors.value = { non_field_errors: ['An unexpected error occurred.'] };
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AccountLayout>
    <form @submit.prevent="onSubmit">
      <FormErrors :errors="errors.non_field_errors || []" />
      <div class="space-y-4">
        <FormField
          v-model="oldPassword"
          label="Current Password"
          type="password"
          autocomplete="current-password"
          :errors="errors.current_password || []"
        />
        <FormField
          v-model="newPassword1"
          label="New Password"
          type="password"
          autocomplete="new-password"
          :errors="errors.new_password || errors.password || errors.password1 || []"
        />
        <FormField
          v-model="newPassword2"
          label="New Password (again)"
          type="password"
          autocomplete="new-password"
          :errors="errors.new_password2 || errors.password2 || []"
        />
      </div>
      <div class="mt-4">
        <button
          type="submit"
          :disabled="loading"
          class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Changing...' : 'Change Password' }}
        </button>
      </div>
    </form>
  </AccountLayout>
</template>
