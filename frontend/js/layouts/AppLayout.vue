<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue';
import { RouterLink } from 'vue-router';
import ThemeToggle from '@/components/ThemeToggle.vue';
import AppToast from '@/components/AppToast.vue';
import TimezoneDetectModal from '@/components/TimezoneDetectModal.vue';
import {
  Cog6ToothIcon,
  ArrowsRightLeftIcon,
  PlusCircleIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  WrenchScrewdriverIcon,
  XCircleIcon,
  UserGroupIcon,
  EnvelopeIcon,
  InboxIcon,
  CircleStackIcon,
} from '@heroicons/vue/24/outline';

const appStore = inject('appStore');
const orgDropdownOpen = ref(false);
const userDropdownOpen = ref(false);
const mobileMenuOpen = ref(false);

const devToolHost = computed(() => window.location.hostname || 'localhost');
const mailpitUrl = computed(() => `http://${devToolHost.value}:8025/`);
const minioUrl = computed(() => `http://${devToolHost.value}:9001/`);

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

function releaseHijack() {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/hijack/release/';
  const csrf = document.createElement('input');
  csrf.type = 'hidden';
  csrf.name = 'csrfmiddlewaretoken';
  csrf.value = getCookie('csrftoken') || '';
  form.appendChild(csrf);
  const next = document.createElement('input');
  next.type = 'hidden';
  next.name = 'next';
  next.value = '/';
  form.appendChild(next);
  document.body.appendChild(form);
  form.submit();
}

function closeAllDropdowns() {
  orgDropdownOpen.value = false;
  userDropdownOpen.value = false;
}

function toggleOrgDropdown() {
  userDropdownOpen.value = false;
  orgDropdownOpen.value = !orgDropdownOpen.value;
}

function toggleUserDropdown() {
  orgDropdownOpen.value = false;
  userDropdownOpen.value = !userDropdownOpen.value;
}

function handleClickOutside(e) {
  if (!e.target.closest('[data-dropdown="nav"]')) {
    closeAllDropdowns();
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<!-- eslint-disable max-len -->
<template>
  <nav class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
    <div class="mx-auto w-full px-4 sm:px-6 lg:px-8">
      <div class="flex h-14 items-center justify-between">
        <div class="flex items-center gap-6">
          <RouterLink
            class="text-lg font-semibold text-gray-900 dark:text-white"
            to="/"
          >
            {{ appStore.siteName }}
          </RouterLink>
        </div>
        <div class="flex items-center gap-1">
          <!-- Org dropdown -->
          <template v-if="appStore.isOrg">
            <div
              class="relative"
              data-dropdown="nav"
            >
              <button
                class="cursor-pointer flex items-center gap-1.5 rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                @click.stop="toggleOrgDropdown"
              >
                {{ appStore.org.name }}
                <svg
                  class="h-4 w-4 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.5"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m19.5 8.25-7.5 7.5-7.5-7.5"
                  />
                </svg>
              </button>
              <div
                v-show="orgDropdownOpen"
                class="absolute right-0 top-full z-50 mt-1 w-56 rounded-md border border-gray-200 bg-white py-1 shadow-lg dark:bg-gray-800 dark:border-gray-700"
              >
                <RouterLink
                  v-if="appStore.isOwner"
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  :to="{ name: 'org-settings-general', params: { slug: appStore.org.slug } }"
                  @click="closeAllDropdowns"
                >
                  <Cog6ToothIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Settings
                </RouterLink>
                <div
                  v-if="appStore.isOwner"
                  class="my-1 border-t border-gray-100 dark:border-gray-700"
                />
                <RouterLink
                  v-if="appStore.orgMemberCount > 0"
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  :to="{ name: 'org-switch' }"
                  @click="closeAllDropdowns"
                >
                  <ArrowsRightLeftIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Switch Company
                </RouterLink>
                <RouterLink
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  :to="{ name: 'org-create' }"
                  @click="closeAllDropdowns"
                >
                  <PlusCircleIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Create Organization
                </RouterLink>
              </div>
            </div>
          </template>
          <template v-else-if="appStore.orgMemberCount > 0">
            <RouterLink
              class="cursor-pointer flex items-center gap-1.5 rounded-md border border-dashed border-gray-300 px-3 py-1.5 text-sm text-gray-500 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-700 dark:border-gray-600 dark:text-gray-400 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-gray-300"
              :to="{ name: 'org-switch' }"
            >
              <ArrowsRightLeftIcon class="h-4 w-4" />
              Switch Organization
            </RouterLink>
          </template>
          <template v-else>
            <RouterLink
              class="cursor-pointer flex items-center gap-1.5 rounded-md border border-dashed border-gray-300 px-3 py-1.5 text-sm text-gray-500 hover:border-gray-400 hover:bg-gray-50 hover:text-gray-700 dark:border-gray-600 dark:text-gray-400 dark:hover:border-gray-500 dark:hover:bg-gray-800 dark:hover:text-gray-300"
              :to="{ name: 'org-create' }"
            >
              <PlusCircleIcon class="h-4 w-4" />
              Create Organization
            </RouterLink>
          </template>

          <!-- User dropdown -->
          <div
            class="relative"
            data-dropdown="nav"
          >
            <button
              class="flex cursor-pointer items-center p-1.5"
              @click.stop="toggleUserDropdown"
            >
              <img
                v-if="appStore.user"
                style="width: 32px; height: 32px"
                :src="appStore.user.avatar_url"
                alt="Profile photo"
                class="rounded-full object-cover transition hover:opacity-80 hover:ring-2 hover:ring-gray-300 dark:hover:ring-gray-600"
              >
            </button>
            <div
              v-show="userDropdownOpen"
              class="absolute right-0 top-full z-50 mt-1 w-56 rounded-md border border-gray-200 bg-white py-1 shadow-lg dark:bg-gray-800 dark:border-gray-700"
            >
              <RouterLink
                class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                :to="{ name: 'account-general' }"
                @click="closeAllDropdowns"
              >
                <UserCircleIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                Account Settings
              </RouterLink>
              <ThemeToggle />
              <div class="my-1 border-t border-gray-100 dark:border-gray-700" />
              <RouterLink
                class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                :to="{ name: 'logout' }"
                @click="closeAllDropdowns"
              >
                <ArrowRightOnRectangleIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                Sign Out
              </RouterLink>
              <template v-if="appStore.user && (appStore.user.is_staff || appStore.user.is_hijacked)">
                <div class="my-1 border-t border-gray-100 dark:border-gray-700" />
                <a
                  v-if="appStore.user.is_staff"
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  href="/admin/"
                >
                  <WrenchScrewdriverIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Administration
                </a>
                <button
                  v-if="appStore.user.is_hijacked"
                  type="button"
                  class="w-full text-left cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  @click="releaseHijack"
                >
                  <XCircleIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Stop Impersonating
                </button>
                <RouterLink
                  v-if="appStore.user.is_staff && !appStore.user.is_hijacked"
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  :to="{ name: 'impersonate' }"
                  @click="closeAllDropdowns"
                >
                  <UserGroupIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Impersonate User
                </RouterLink>
                <RouterLink
                  v-if="appStore.user.is_superuser && !appStore.user.is_hijacked"
                  class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  :to="{ name: 'send-test-emails' }"
                  @click="closeAllDropdowns"
                >
                  <EnvelopeIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Send Test Email
                </RouterLink>
                <template v-if="appStore.user.is_superuser && appStore.instance !== 'prod'">
                  <a
                    class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                    :href="mailpitUrl"
                    target="_blank"
                    rel="noopener"
                  >
                    <InboxIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    Mailpit
                  </a>
                  <a
                    class="cursor-pointer flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                    :href="minioUrl"
                    target="_blank"
                    rel="noopener"
                  >
                    <CircleStackIcon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    MinIO Admin
                  </a>
                </template>
              </template>
            </div>
          </div>

          <!-- Mobile hamburger -->
          <button
            class="lg:hidden cursor-pointer rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <svg
              class="h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile menu -->
      <div
        v-if="mobileMenuOpen"
        class="lg:hidden border-t border-gray-200 py-2 dark:border-gray-700"
      >
        <template v-if="appStore.isOrg">
          <div class="px-2 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ appStore.org.name }}
          </div>
          <RouterLink
            v-if="appStore.isOwner"
            class="block px-2 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 rounded cursor-pointer"
            :to="{ name: 'org-settings-general', params: { slug: appStore.org.slug } }"
            @click="mobileMenuOpen = false"
          >
            Settings
          </RouterLink>
          <RouterLink
            class="block px-2 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 rounded cursor-pointer"
            :to="{ name: 'org-create' }"
            @click="mobileMenuOpen = false"
          >
            Create Organization
          </RouterLink>
          <div class="my-1 border-t border-gray-200 dark:border-gray-700" />
        </template>
      </div>
    </div>
  </nav>

  <main class="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 mt-6 pb-8 flex-1">
    <slot />
  </main>

  <AppToast />
  <TimezoneDetectModal />
</template>
