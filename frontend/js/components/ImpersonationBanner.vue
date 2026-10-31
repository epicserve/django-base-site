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
          class="impersonation-banner__strip border-b border-[#3a2a00]/15 bg-[#ffc23d] text-[#3a2a00] dark:border-black/40 dark:bg-[#f0b429]"
        >
          <div class="mx-auto flex h-11 w-full items-center gap-3 px-4 sm:px-6 lg:px-8">
            <UserAvatar
              :src="user.avatar_url || ''"
              :name="displayName"
              size="md"
              class="shrink-0 ring-2 ring-[#3a2a00]/25"
            />
            <p class="min-w-0 flex-1 truncate text-sm">
              You're impersonating <strong class="font-semibold">{{ displayName }}</strong>
              <span v-if="fullName && user.email" class="ml-1.5 hidden text-[#3a2a00]/70 sm:inline">
                {{ user.email }}
              </span>
            </p>
            <button
              type="button"
              class="shrink-0 cursor-pointer rounded-full bg-[#3a2a00] px-3 py-1 text-xs font-semibold text-[#ffd873] shadow-sm transition-colors hover:bg-[#1f1600] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#3a2a00]"
              @click="stopImpersonating"
            >
              <span class="sm:hidden">Stop</span>
              <span class="hidden sm:inline">Stop Impersonating</span>
            </button>
            <button
              type="button"
              class="-mr-1.5 shrink-0 cursor-pointer rounded-full p-1.5 text-[#3a2a00]/70 transition-colors hover:bg-[#3a2a00]/10 hover:text-[#3a2a00] focus-visible:outline-2 focus-visible:outline-[#3a2a00]"
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
/* A faint hazard-tape hatch, so the strip reads as "not your normal session" at a glance. */
.impersonation-banner__strip {
  background-image: repeating-linear-gradient(-45deg, rgb(58 42 0 / 0.06) 0 10px, transparent 10px 20px);
}

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
