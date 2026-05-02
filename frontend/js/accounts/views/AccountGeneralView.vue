<script setup>
import { ref, inject } from 'vue';
import AccountLayout from '@/layouts/AccountLayout.vue';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import AvatarCropper from '../../components/AvatarCropper.vue';
import TimezoneSelectApp from '../../apps/TimezoneSelectApp.vue';
import { patch, parseErrors } from '../../utils/api';
import { showToast } from '../../composables/useToast';

const appStore = inject('appStore');

const firstName = ref(appStore.user?.first_name || '');
const lastName = ref(appStore.user?.last_name || '');
const timezone = ref(appStore.user?.timezone || '');
const errors = ref({});
const loading = ref(false);

function onTimezoneChange(value) {
  timezone.value = value;
}

async function onSubmit() {
  loading.value = true;
  errors.value = {};
  try {
    const data = await patch(`/api/users/${appStore.user.id}/`, {
      first_name: firstName.value,
      last_name: lastName.value,
      timezone: timezone.value,
    });

    appStore.setUser({ ...appStore.user, ...data });
    showToast('Your settings were updated.');
  } catch (err) {
    errors.value = parseErrors(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AccountLayout>
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Profile Photo</label>
      <AvatarCropper
        :current-avatar-url="appStore.user?.avatar_url || ''"
        upload-url="/api/avatar/"
      />
    </div>
    <form @submit.prevent="onSubmit">
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField
        v-model="firstName"
        label="First name"
        autocomplete="given-name"
        :errors="errors.first_name || []"
      />
      <FormField
        v-model="lastName"
        label="Last name"
        autocomplete="family-name"
        :errors="errors.last_name || []"
      />
      <div class="mb-4 mt-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Timezone</label>
        <TimezoneSelectApp
          :current-timezone="timezone"
          field-name="timezone"
          :model-value="timezone"
          @update:model-value="onTimezoneChange"
        />
      </div>
      <div class="mt-4">
        <button
          type="submit"
          :disabled="loading"
          class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </form>
  </AccountLayout>
</template>
