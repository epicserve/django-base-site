<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import AccountLayout from '@/layouts/AccountLayout.vue';
import FormField from '../components/FormField.vue';
import { authApi, parseAllauthErrors } from '../api';
import { showToast } from '../../composables/useToast';
import { createPasskeyCredential, isWebAuthnSupported } from '../../utils/webauthn';

const router = useRouter();
const passkeys = ref([]);
const newName = ref('');
const passwordless = ref(true);
const errors = ref({});
const loading = ref(true);
const supported = ref(true);

async function load() {
  loading.value = true;
  try {
    const data = await authApi.listAuthenticators();

    passkeys.value = (data.data || []).filter((a) => a.type === 'webauthn');
  } catch (err) {
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/passkeys/' } });
    }
  } finally {
    loading.value = false;
  }
}

async function add() {
  errors.value = {};
  loading.value = true;
  try {
    const optsResp = await authApi.beginAddPasskey(passwordless.value);
    const options = optsResp.data?.creation_options || optsResp.data;
    const rpId = options?.publicKey?.rp?.id || options?.rp?.id;
    // eslint-disable-next-line no-console
    console.info('[passkey enroll] page origin:', window.location.origin, '/ rp.id:', rpId);
    const credential = await createPasskeyCredential(options);

    await authApi.addPasskey(newName.value || 'Passkey', credential);
    showToast('Passkey added.');
    newName.value = '';
    await load();
  } catch (err) {
    if (err.name === 'NotAllowedError' || err.name === 'AbortError') {
      // user cancelled
      return;
    }
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/passkeys/' } });
      return;
    }
    errors.value = err.data ? parseAllauthErrors(err.data) : {
      non_field_errors: [err.message || 'Failed to add passkey.'],
    };
  } finally {
    loading.value = false;
  }
}

async function rename(pk) {
  const name = prompt('New name for this passkey?', pk.name);

  if (!name || name === pk.name) return;
  try {
    await authApi.renamePasskey(pk.id, name);
    showToast('Passkey renamed.');
    await load();
  } catch (err) {
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/passkeys/' } });
    }
  }
}

async function remove(pk) {
  if (!confirm(`Remove the passkey "${pk.name}"?`)) return;
  try {
    await authApi.removePasskey(pk.id);
    showToast('Passkey removed.');
    await load();
  } catch (err) {
    if (err.response?.status === 401) {
      router.push({ name: 'account-reauthenticate', query: { next: '/accounts/security/passkeys/' } });
    }
  }
}

onMounted(() => {
  supported.value = isWebAuthnSupported();
  load();
});
</script>

<template>
  <AccountLayout>
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
      Passkeys
    </h2>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Sign in with Touch ID, Windows Hello, your phone, or a hardware key.
    </p>

    <p
      v-if="!supported"
      class="rounded-md bg-yellow-50 dark:bg-yellow-900/20 px-3 py-2 text-sm text-yellow-800 dark:text-yellow-200 mb-4"
    >
      This browser doesn't support passkeys.
    </p>

    <div
      v-if="passkeys.length"
      class="space-y-2 mb-6"
    >
      <div
        v-for="pk in passkeys"
        :key="pk.id"
        class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3"
      >
        <div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            {{ pk.name }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            <span v-if="pk.is_passwordless">Passwordless</span>
            <span v-else>Two-factor</span>
            · Added {{ new Date(pk.created_at * 1000).toLocaleDateString() }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="cursor-pointer rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
            @click="rename(pk)"
          >
            Rename
          </button>
          <button
            type="button"
            class="cursor-pointer rounded-md px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
            @click="remove(pk)"
          >
            Remove
          </button>
        </div>
      </div>
    </div>

    <form
      v-if="supported"
      class="space-y-3 max-w-md rounded-lg border border-gray-200 dark:border-gray-700 p-4"
      @submit.prevent="add"
    >
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
        Add a passkey
      </h3>
      <FormField
        v-model="newName"
        label="Name"
        placeholder="MacBook, YubiKey, iPhone…"
        :errors="errors.name || []"
      />
      <label class="flex items-start gap-2 cursor-pointer">
        <input
          v-model="passwordless"
          type="checkbox"
          class="mt-0.5 cursor-pointer text-blue-600 focus:ring-blue-500"
        >
        <span class="text-sm text-gray-700 dark:text-gray-300">
          Allow this passkey to sign me in without a password
        </span>
      </label>
      <p
        v-for="e in (errors.non_field_errors || [])"
        :key="e"
        class="text-sm text-red-600 dark:text-red-400"
      >
        {{ e }}
      </p>
      <button
        type="submit"
        :disabled="loading"
        class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Adding…' : 'Add passkey' }}
      </button>
    </form>
  </AccountLayout>
</template>
