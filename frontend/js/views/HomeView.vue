<script setup>
import { computed, inject } from 'vue';
import { RouterLink } from 'vue-router';
import {
  ArrowUpRightIcon,
  Cog6ToothIcon,
  PlusCircleIcon,
  WrenchScrewdriverIcon,
  InboxIcon,
  CircleStackIcon,
  CodeBracketIcon,
} from '@heroicons/vue/24/outline';

const appStore = inject('appStore');

const greeting = computed(() => {
  const name = appStore.user?.first_name?.trim();
  return name ? `Welcome, ${name}.` : 'Welcome.';
});

const orgLine = computed(() => {
  if (appStore.org?.name) return `You're working in ${appStore.org.name}.`;
  if (appStore.organizations?.length) return 'Pick an organization or create another to get started.';
  return 'Spin up your first organization to start building.';
});

const isDev = computed(() => appStore.instance !== 'prod');
const isStaff = computed(() => !!appStore.user?.is_staff);
const isSuperuser = computed(() => !!appStore.user?.is_superuser);

const stack = [
  { label: 'Authentication',     value: 'django-allauth · headless · MFA + passkeys' },
  { label: 'Multi-tenant',       value: 'organizations · teams · invites' },
  { label: 'API',                value: 'django-ninja' },
  { label: 'Database',           value: 'PostgreSQL 17' },
  { label: 'Cache & sessions',   value: 'Redis 7' },
  { label: 'Background tasks',   value: 'Celery (Redis broker)' },
  { label: 'Object storage',     value: 'MinIO · S3-compatible' },
  { label: 'Email',              value: 'Mailpit (dev) · django-ses (prod)' },
  { label: 'Frontend',           value: 'Vue 3 · Tailwind v4 · Vite · bun' },
  { label: 'WSGI server',        value: 'gunicorn (4 × 2)' },
];

const devToolHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
const mailpitUrl = `http://${devToolHost}:8025/`;
const minioUrl = `http://${devToolHost}:9001/`;
</script>

<template>
  <div class="welcome relative">
    <!-- decorative grid -->
    <div
      aria-hidden="true"
      class="welcome__grid pointer-events-none absolute inset-0 -z-10 opacity-40 dark:opacity-30"
    />

    <div class="mx-auto max-w-6xl pt-14 pb-24 sm:pt-20 lg:pt-24">
      <!-- masthead -->
      <header class="welcome__reveal">
        <h1 class="welcome__title font-display text-5xl text-gray-900 sm:text-6xl lg:text-7xl dark:text-white">
          {{ greeting }}
        </h1>

        <p class="mt-5 max-w-2xl text-lg text-gray-600 dark:text-gray-300">
          {{ orgLine }}
        </p>
      </header>

      <!-- stack manifest -->
      <section class="welcome__reveal welcome__reveal--2 mt-16">
        <div class="flex items-baseline gap-4 mb-5">
          <span class="font-mono text-[10px] uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400">
            What's wired up
          </span>
          <span class="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
        </div>

        <dl class="grid grid-cols-1 gap-x-10 gap-y-0 sm:grid-cols-2">
          <div
            v-for="(row, idx) in stack"
            :key="row.label"
            class="welcome__row group flex items-baseline gap-4 border-b border-gray-200/70 py-3.5 dark:border-gray-800/80"
          >
            <span class="welcome__index font-mono text-[10px] tabular-nums text-gray-400 dark:text-gray-600">
              {{ String(idx + 1).padStart(2, '0') }}
            </span>
            <dt class="text-sm font-medium text-gray-900 dark:text-gray-100 min-w-[10ch]">
              {{ row.label }}
            </dt>
            <dd class="ml-auto text-right text-sm text-gray-500 dark:text-gray-400">
              {{ row.value }}
            </dd>
          </div>
        </dl>
      </section>

      <!-- next steps -->
      <section class="welcome__reveal welcome__reveal--3 mt-16">
        <div class="flex items-baseline gap-4 mb-5">
          <span class="font-mono text-[10px] uppercase tracking-[0.22em] text-gray-500 dark:text-gray-400">
            Next
          </span>
          <span class="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
        </div>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <RouterLink
            v-if="!appStore.isOrg"
            :to="{ name: 'org-create' }"
            class="welcome__card group"
          >
            <PlusCircleIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                Create an organization
              </div>
              <div class="welcome__card-sub">
                Multi-tenant scaffolding, ready to use.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </RouterLink>

          <RouterLink
            :to="{ name: 'account-general' }"
            class="welcome__card group"
          >
            <Cog6ToothIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                Account settings
              </div>
              <div class="welcome__card-sub">
                Profile, email, password, security.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </RouterLink>

          <a
            v-if="isStaff"
            href="/admin/"
            class="welcome__card group"
          >
            <WrenchScrewdriverIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                Django admin
              </div>
              <div class="welcome__card-sub">
                Inspect users, orgs, sessions.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </a>

          <a
            v-if="isSuperuser && isDev"
            href="/api/docs"
            target="_blank"
            rel="noopener"
            class="welcome__card group"
          >
            <CodeBracketIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                API docs
              </div>
              <div class="welcome__card-sub">
                Live OpenAPI spec for the ninja API.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </a>

          <a
            v-if="isSuperuser && isDev"
            :href="mailpitUrl"
            target="_blank"
            rel="noopener"
            class="welcome__card group"
          >
            <InboxIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                Mailpit
              </div>
              <div class="welcome__card-sub">
                Inspect outgoing emails locally.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </a>

          <a
            v-if="isSuperuser && isDev"
            :href="minioUrl"
            target="_blank"
            rel="noopener"
            class="welcome__card group"
          >
            <CircleStackIcon class="welcome__card-icon" />
            <div>
              <div class="welcome__card-title">
                MinIO console
              </div>
              <div class="welcome__card-sub">
                Browse media bucket contents.
              </div>
            </div>
            <ArrowUpRightIcon class="welcome__card-arrow" />
          </a>
        </div>
      </section>

      <!-- colophon -->
      <footer class="welcome__reveal welcome__reveal--4 mt-20 flex flex-wrap items-baseline gap-x-4 gap-y-1 font-mono text-[10px] uppercase tracking-[0.2em] text-gray-400 dark:text-gray-600">
        <span>{{ appStore.instance }}</span>
        <span class="text-gray-300 dark:text-gray-700">·</span>
        <span>django + vue</span>
        <span class="text-gray-300 dark:text-gray-700">·</span>
        <span>{{ new Date().getUTCFullYear() }}</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  isolation: isolate;
}

.welcome__grid {
  background-image:
    linear-gradient(to right, rgb(0 0 0 / 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgb(0 0 0 / 0.04) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 80% 60% at 30% 0%, black, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 30% 0%, black, transparent 70%);
}

:where([data-theme="dark"]) .welcome__grid {
  background-image:
    linear-gradient(to right, rgb(255 255 255 / 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgb(255 255 255 / 0.04) 1px, transparent 1px);
}

.welcome__title {
  font-weight: 350;
  font-variation-settings: "opsz" 144, "SOFT" 25;
  letter-spacing: -0.02em;
  line-height: 1;
}

.welcome__row:last-child {
  border-bottom: 0;
}
.welcome__row:hover .welcome__index {
  color: rgb(37 99 235); /* blue-600 */
}
:where([data-theme="dark"]) .welcome__row:hover .welcome__index {
  color: rgb(96 165 250); /* blue-400 */
}

.welcome__card {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem 1.125rem;
  border-radius: 0.625rem;
  border: 1px solid rgb(229 231 235); /* gray-200 */
  background: rgb(255 255 255 / 0.5);
  transition: border-color 150ms ease, transform 150ms ease, background-color 150ms ease;
  text-decoration: none;
}
:where([data-theme="dark"]) .welcome__card {
  border-color: rgb(31 41 55); /* gray-800 */
  background: rgb(17 24 39 / 0.4); /* gray-900/40 */
}
.welcome__card:hover {
  border-color: rgb(96 165 250); /* blue-400 */
  background: rgb(239 246 255 / 0.7); /* blue-50 */
}
:where([data-theme="dark"]) .welcome__card:hover {
  border-color: rgb(59 130 246); /* blue-500 */
  background: rgb(30 58 138 / 0.15); /* blue-900/15 */
}

.welcome__card-icon {
  flex-shrink: 0;
  width: 1.125rem;
  height: 1.125rem;
  color: rgb(107 114 128); /* gray-500 */
  transition: color 150ms ease;
}
:where([data-theme="dark"]) .welcome__card-icon {
  color: rgb(156 163 175); /* gray-400 */
}
.welcome__card:hover .welcome__card-icon {
  color: rgb(37 99 235);
}
:where([data-theme="dark"]) .welcome__card:hover .welcome__card-icon {
  color: rgb(96 165 250);
}

.welcome__card-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(17 24 39); /* gray-900 */
}
:where([data-theme="dark"]) .welcome__card-title {
  color: rgb(243 244 246); /* gray-100 */
}

.welcome__card-sub {
  font-size: 0.75rem;
  color: rgb(107 114 128);
  margin-top: 0.125rem;
}
:where([data-theme="dark"]) .welcome__card-sub {
  color: rgb(156 163 175);
}

.welcome__card-arrow {
  margin-left: auto;
  width: 0.875rem;
  height: 0.875rem;
  color: rgb(156 163 175);
  transform: translate(0, 0);
  transition: transform 200ms ease, color 150ms ease;
}
.welcome__card:hover .welcome__card-arrow {
  color: rgb(37 99 235);
  transform: translate(2px, -2px);
}
:where([data-theme="dark"]) .welcome__card:hover .welcome__card-arrow {
  color: rgb(96 165 250);
}

/* Staggered reveal on initial render */
@keyframes welcomeRise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome__reveal {
  animation: welcomeRise 700ms cubic-bezier(0.16, 1, 0.3, 1) both;
}
.welcome__reveal--2 { animation-delay: 100ms; }
.welcome__reveal--3 { animation-delay: 220ms; }
.welcome__reveal--4 { animation-delay: 360ms; }

@media (prefers-reduced-motion: reduce) {
  .welcome__reveal {
    animation: none;
  }
}
</style>
