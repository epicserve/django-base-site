<script setup lang="ts">
import { ref, computed } from 'vue';
import AccountLayout from '@/layouts/AccountLayout.vue';
import { useAppStore } from '@/stores/app';
import FormField from '../components/FormField.vue';
import FormErrors from '../components/FormErrors.vue';
import AvatarCropper from '../../components/AvatarCropper.vue';
import TimezoneSelectApp from '../../apps/TimezoneSelectApp.vue';
import { api, parseErrors, unwrap } from '../../utils/api';
import { showToast } from '../../composables/useToast';

const appStore = useAppStore();

const userDisplayName = computed(() => {
  const fullName = `${appStore.user?.first_name || ''} ${appStore.user?.last_name || ''}`.trim();
  return fullName || appStore.user?.email || '';
});

const firstName = ref(appStore.user?.first_name || '');
const lastName = ref(appStore.user?.last_name || '');
const timezone = ref(appStore.user?.timezone || '');
const errors = ref<Record<string, string[]>>({});
const loading = ref(false);

function onTimezoneChange(value: string) {
  timezone.value = value;
}

async function onSubmit() {
  if (!appStore.user) return;
  loading.value = true;
  errors.value = {};
  try {
    const data = await unwrap(
      api.PATCH('/api/users/{user_id}/', {
        params: { path: { user_id: appStore.user.id } },
        body: {
          first_name: firstName.value,
          last_name: lastName.value,
          timezone: timezone.value,
        },
      }),
    );

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
      <h2 class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Profile Photo</h2>
      <AvatarCropper :current-avatar-url="appStore.user?.avatar_url || ''" :user-name="userDisplayName" />
    </div>
    <form @submit.prevent="onSubmit">
      <FormErrors :errors="errors.non_field_errors || []" />
      <FormField v-model="firstName" label="First Name" autocomplete="given-name" :errors="errors.first_name || []" />
      <FormField v-model="lastName" label="Last Name" autocomplete="family-name" :errors="errors.last_name || []" />
      <div class="mb-4 mt-4">
        <label for="timezone-search" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >Timezone</label
        >
        <TimezoneSelectApp
          input-id="timezone-search"
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
