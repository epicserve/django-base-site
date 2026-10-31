<script setup>
import { computed, inject } from 'vue';
import { XMarkIcon } from '@heroicons/vue/20/solid';
import UserAvatar from '@/components/UserAvatar.vue';
import { post } from '@/utils/api';
import { stopImpersonating } from '@/utils/hijack';

const appStore = inject('appStore');

const user = computed(() => appStore.user);
const fullName = computed(() => `${user.value?.first_name || ''} ${user.value?.last_name || ''}`.trim());
const displayName = computed(() => fullName.value || user.value?.email || user.value?.username || '');
const visible = computed(() => !!user.value?.is_hijacked && !user.value.impersonation_banner_hidden);

// Hidden for the rest of this impersonation. The flag lives in the Django session, which is
// flushed when the next impersonation logs in a different user, so the banner comes back then.
async function hide() {
  appStore.user.impersonation_banner_hidden = true;
  try {
    await post('/api/impersonation/hide-banner/');
  } catch {
    // Already hidden on this page; it shows again on the next page load.
  }
}
</script>

<template>
  <Transition name="impersonation-banner">
    <div v-if="visible" class="impersonation-banner grid">
      <div class="overflow-hidden">
        <div
          role="status"
          class="border-b border-blue-200 bg-blue-50 text-sm text-blue-900 dark:border-blue-700/40 dark:bg-blue-900/20 dark:text-blue-200"
        >
          <div class="mx-auto flex h-10 w-full items-center gap-2.5 px-4 sm:px-6 lg:px-8">
            <UserAvatar :src="user.avatar_url || ''" :name="displayName" size="md" class="shrink-0" />
            <!-- Vue drops whitespace-only text next to tags, so the &nbsp; keeps a space before the email. -->
            <p class="min-w-0 flex-1 truncate">
              Impersonating
              <strong class="font-semibold">{{ displayName }}</strong>
              <span v-if="fullName && user.email" class="hidden text-blue-800/70 sm:inline dark:text-blue-300/70">
                &nbsp;{{ user.email }}
              </span>
            </p>
            <button
              type="button"
              class="shrink-0 cursor-pointer rounded-md border border-gray-300 bg-white px-2.5 py-0.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              @click="stopImpersonating"
            >
              <span class="sm:hidden">Stop</span>
              <span class="hidden sm:inline">Stop Impersonating</span>
            </button>
            <button
              type="button"
              class="-mr-1 shrink-0 cursor-pointer rounded p-1 hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-blue-600 dark:hover:bg-blue-900/40"
              aria-label="Hide Banner"
              title="Hide until you impersonate someone again"
              @click="hide"
            >
              <XMarkIcon class="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Collapse the row when it's hidden instead of letting the nav jump up. */
.impersonation-banner {
  grid-template-rows: 1fr;
}

.impersonation-banner-leave-active {
  transition:
    grid-template-rows 200ms ease,
    opacity 200ms ease;
}

.impersonation-banner-leave-to {
  grid-template-rows: 0fr;
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .impersonation-banner-leave-active {
    transition: none;
  }
}
</style>
