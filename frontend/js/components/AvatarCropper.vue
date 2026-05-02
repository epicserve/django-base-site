<script setup>
import { ref, computed, inject } from 'vue';
import { Cropper } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';
import AppModal from './AppModal.vue';
import UserAvatar from './UserAvatar.vue';
import { postFormData, deleteRequest } from '../utils/api.js';

const props = defineProps({
  currentAvatarUrl: { type: String, default: '' },
  userName: { type: String, default: '' },
  uploadUrl: { type: String, required: true },
});

const appStore = inject('appStore', null);

const avatarUrl = ref(props.currentAvatarUrl);
const showModal = ref(false);
const imageFile = ref(null);
const imageSrc = ref(null);
const cropperRef = ref(null);
const loading = ref(false);
const error = ref('');
let activeReader = null;

const hasAvatar = computed(() => Boolean(avatarUrl.value));

function onFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) {
    error.value = 'Please select a JPEG, PNG, or WebP image.';
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    error.value = 'Image must be under 10 MB.';
    return;
  }

  error.value = '';
  imageFile.value = file;
  // Cancel an earlier read in case the user picked a file in rapid succession;
  // otherwise the older onload could fire after the newer one and clobber
  // imageSrc with the previous selection.
  if (activeReader) activeReader.abort();
  const reader = new FileReader();
  activeReader = reader;

  reader.onload = (e) => {
    if (activeReader === reader) {
      imageSrc.value = e.target.result;
      activeReader = null;
    }
  };
  reader.readAsDataURL(file);
}

function openModal() {
  imageSrc.value = null;
  imageFile.value = null;
  error.value = '';
  showModal.value = true;
}

function closeModal() {
  showModal.value = false;
  imageSrc.value = null;
  imageFile.value = null;
  error.value = '';
}

async function save() {
  if (!imageFile.value || !cropperRef.value) return;

  loading.value = true;
  error.value = '';

  try {
    const { coordinates } = cropperRef.value.getResult();
    const formData = new FormData();

    formData.append('image', imageFile.value);
    formData.append('crop_data', JSON.stringify({
      left: Math.round(coordinates.left),
      top: Math.round(coordinates.top),
      width: Math.round(coordinates.width),
      height: Math.round(coordinates.height),
    }));

    const data = await postFormData(props.uploadUrl, formData);

    avatarUrl.value = data.avatar_url;
    if (appStore?.user) {
      appStore.setUser({ ...appStore.user, avatar_url: data.avatar_url });
    }
    closeModal();
  } catch (err) {
    error.value = err.data?.image?.[0] || 'Upload failed. Please try again.';
  } finally {
    loading.value = false;
  }
}

async function removeAvatar() {
  loading.value = true;
  error.value = '';

  try {
    await deleteRequest(props.uploadUrl);
    avatarUrl.value = '';
    if (appStore?.user) {
      appStore.setUser({ ...appStore.user, avatar_url: null });
    }
  } catch {
    error.value = 'Failed to remove avatar.';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex items-center gap-4">
    <img
      v-if="hasAvatar"
      :src="avatarUrl"
      alt="Profile photo"
      class="h-16 w-16 rounded-full object-cover"
    >
    <UserAvatar
      v-else
      :name="userName"
      size="rail"
      class="!h-16 !w-16 !text-base"
    />
    <div class="flex gap-2">
      <button
        type="button"
        class="cursor-pointer rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="openModal"
      >
        Change photo
      </button>
      <button
        v-if="hasAvatar"
        type="button"
        class="cursor-pointer rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20"
        :disabled="loading"
        @click="removeAvatar"
      >
        Remove
      </button>
    </div>
  </div>

  <AppModal
    :open="showModal"
    title="Change profile photo"
    size="lg"
    @close="closeModal"
  >
    <div
      v-if="!imageSrc"
      class="text-center py-8"
    >
      <label
        class="cursor-pointer inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        <svg
          class="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        Choose an image
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          class="hidden"
          @change="onFileSelect"
        >
      </label>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        JPEG, PNG, or WebP up to 10 MB
      </p>
    </div>

    <div v-else>
      <Cropper
        ref="cropperRef"
        :src="imageSrc"
        :stencil-props="{ aspectRatio: 1 }"
        class="h-80"
      />
    </div>

    <p
      v-if="error"
      class="mt-2 text-sm text-red-600"
    >
      {{ error }}
    </p>

    <template
      v-if="imageSrc"
      #footer
    >
      <button
        type="button"
        class="cursor-pointer rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="closeModal"
      >
        Cancel
      </button>
      <button
        type="button"
        class="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        :disabled="loading"
        @click="save"
      >
        {{ loading ? 'Saving...' : 'Save' }}
      </button>
    </template>
  </AppModal>
</template>
