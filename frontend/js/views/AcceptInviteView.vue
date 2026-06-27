<script setup>
import { ref, inject, onMounted } from 'vue';
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { get, post } from '@/utils/api';
import AuthLayout from '@/layouts/AuthLayout.vue';

const route = useRoute();
const router = useRouter();
const appStore = inject('appStore');

const loading = ref(true);
const submitting = ref(false);
const invite = ref(null);
const error = ref('');
const result = ref(''); // 'accepted' | 'declined' | ''

async function loadInvite() {
  try {
    invite.value = await get(`/api/invite-by-key/${route.params.key}/`);
  } catch (e) {
    error.value = e.response?.status === 404 ? 'This invitation link is invalid.' : 'Could not load this invitation.';
  } finally {
    loading.value = false;
  }
}

async function accept() {
  if (!appStore.isAuthenticated) {
    router.push({ name: 'login', query: { next: route.fullPath } });
    return;
  }
  submitting.value = true;
  try {
    await post(`/api/invite-by-key/${route.params.key}/accept/`);
    await appStore.fetchContext();
    result.value = 'accepted';
  } catch (e) {
    error.value = e.message || 'Failed to accept the invitation.';
  } finally {
    submitting.value = false;
  }
}

async function decline() {
  submitting.value = true;
  try {
    await post(`/api/invite-by-key/${route.params.key}/decline/`);
    result.value = 'declined';
  } catch (e) {
    error.value = e.message || 'Failed to decline the invitation.';
  } finally {
    submitting.value = false;
  }
}

function goToSignup() {
  router.push({ name: 'signup', query: { next: route.fullPath } });
}

function goToLogin() {
  router.push({ name: 'login', query: { next: route.fullPath } });
}

onMounted(loadInvite);
</script>

<template>
  <AuthLayout>
    <div v-if="loading" class="text-center text-sm text-gray-400">Loading invitation...</div>

    <div v-else-if="error" class="text-center">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-white">Invitation unavailable</h1>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        {{ error }}
      </p>
    </div>

    <div v-else-if="result === 'accepted'" class="text-center">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-white">You've joined {{ invite.organization_name }}!</h1>
      <RouterLink
        class="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        :to="{ name: 'home' }"
      >
        Continue
      </RouterLink>
    </div>

    <div v-else-if="result === 'declined'" class="text-center">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-white">Invitation declined</h1>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">You can close this page.</p>
    </div>

    <div v-else-if="invite.is_expired" class="text-center">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-white">Invitation expired</h1>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        Ask {{ invite.sender_name }} to send you a new invitation.
      </p>
    </div>

    <div v-else-if="invite.is_already_member" class="text-center">
      <h1 class="text-xl font-semibold text-gray-900 dark:text-white">Already a member</h1>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        You're already a member of {{ invite.organization_name }}.
      </p>
      <RouterLink
        class="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        :to="{ name: 'home' }"
      >
        Continue
      </RouterLink>
    </div>

    <div v-else>
      <h1 class="text-center text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">You're invited!</h1>
      <p class="mt-2 text-center text-sm text-gray-500 dark:text-gray-400">
        <strong>{{ invite.sender_name }}</strong> invited you to join <strong>{{ invite.organization_name }}</strong
        >.
      </p>

      <div v-if="appStore.isAuthenticated" class="mt-6 space-y-2">
        <button
          type="button"
          class="w-full cursor-pointer rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          :disabled="submitting"
          @click="accept"
        >
          Accept invitation
        </button>
        <button
          type="button"
          class="w-full cursor-pointer rounded-md border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50"
          :disabled="submitting"
          @click="decline"
        >
          Decline
        </button>
      </div>

      <div v-else class="mt-6 space-y-2">
        <button
          type="button"
          class="w-full cursor-pointer rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          @click="goToSignup"
        >
          Create an account to join
        </button>
        <button
          type="button"
          class="w-full cursor-pointer rounded-md border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="goToLogin"
        >
          I already have an account
        </button>
      </div>
    </div>
  </AuthLayout>
</template>
