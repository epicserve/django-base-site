<script setup>
import { computed, inject } from 'vue';

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

@media (prefers-reduced-motion: reduce) {
  .welcome__reveal {
    animation: none;
  }
}
</style>
