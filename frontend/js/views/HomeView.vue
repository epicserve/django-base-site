<script>
// Module scope, so the tower drops in once per page load rather than every time
// the router remounts this view.
let towerHasDropped = false;
</script>

<script setup>
import { computed, inject, ref } from 'vue';
import { ArrowTopRightOnSquareIcon, CodeBracketIcon } from '@heroicons/vue/20/solid';

const appStore = inject('appStore');

const shouldDrop = !towerHasDropped;
towerHasDropped = true;

const docsUrl = 'https://django-base-site.readthedocs.io/en/latest/';

const greeting = computed(() => {
  const name = appStore.user?.first_name?.trim();
  return `Hi ${name || 'there'}, let's build something.`;
});

// Top of the tower first, so the list reads in the same order as the picture.
const layers = [
  {
    key: 'frontend',
    name: 'Vue front end',
    color: '#2bd19e',
    labelColor: '#0f2e24',
    description: 'A single-page app styled with Tailwind and hot-reloaded by Vite while you work.',
    parts: ['Vue 3', 'Vue Router', 'Tailwind v4', 'Vite', 'bun'],
  },
  {
    key: 'teams',
    name: 'Teams & billing',
    color: '#ffc23d',
    labelColor: '#3a2a00',
    description:
      'Organizations with members, teams, and email invites, plus in-app notifications and optional Stripe subscriptions.',
    parts: ['Organizations', 'Teams', 'Invites', 'Notifications', 'Stripe'],
  },
  {
    key: 'auth',
    name: 'Sign-in & security',
    color: '#ff6f9a',
    labelColor: '#3d0618',
    description: 'Sign-up, email verification, and password reset, with two-factor codes and passkeys.',
    parts: ['django-allauth', 'Two-factor codes', 'Passkeys', 'Recovery codes'],
  },
  {
    key: 'django',
    name: 'Django & API',
    color: '#7c5cfa',
    labelColor: '#ffffff',
    description: 'Django 6 with a JSON API at /api/, Celery for background jobs, and gunicorn for production.',
    parts: ['Django 6', 'django-ninja', 'Celery', 'gunicorn', 'WhiteNoise'],
  },
  {
    key: 'services',
    name: 'Services',
    color: '#2563eb',
    labelColor: '#ffffff',
    description:
      'Postgres, Redis, S3-compatible file storage, and a local inbox for email, all started by Docker Compose.',
    parts: ['PostgreSQL 17', 'Redis 7', 'Silo', 'Mailpit', 'Docker'],
  },
];

// ---- Isometric tower geometry -------------------------------------------------
// A point (x, y, z) projects to screen as ((x - y)·cos30°, (x + y)·sin30° − z).
const COS = Math.cos(Math.PI / 6);
const SIN = 0.5;
const iso = (x, y, z) => [(x - y) * COS, (x + y) * SIN - z];
const points = (corners) =>
  corners
    .map((c) =>
      iso(...c)
        .map((n) => n.toFixed(1))
        .join(','),
    )
    .join(' ');

const LENGTH = 220; // along x: the long face that carries the label
const DEPTH = 100; // along y
const PULL = 40; // how far a block slides toward you when its row is pointed at
const GHOST_GAP = 18; // the empty "your app" block floats this far above the stack

// Bottom to top, with a little jitter so it looks stacked by hand.
const stackPlan = [
  { key: 'services', height: 60, dx: 0, dy: 0 },
  { key: 'django', height: 52, dx: 12, dy: -8 },
  { key: 'auth', height: 54, dx: -6, dy: 6 },
  { key: 'teams', height: 50, dx: 14, dy: 0 },
  { key: 'frontend', height: 54, dx: 2, dy: -4 },
];

function buildBlock({ dx, dy, z0, height }) {
  const x0 = dx;
  const y0 = dy;
  const x1 = x0 + LENGTH;
  const y1 = y0 + DEPTH;
  const z1 = z0 + height;
  const [lx, ly] = iso(x0 + 20, y1, z0 + height / 2);
  return {
    top: points([
      [x0, y0, z1],
      [x1, y0, z1],
      [x1, y1, z1],
      [x0, y1, z1],
    ]),
    front: points([
      [x0, y1, z0],
      [x1, y1, z0],
      [x1, y1, z1],
      [x0, y1, z1],
    ]),
    side: points([
      [x1, y0, z0],
      [x1, y1, z0],
      [x1, y1, z1],
      [x1, y0, z1],
    ]),
    // The block's silhouette, for the hover hit area.
    outline: points([
      [x0, y0, z1],
      [x1, y0, z1],
      [x1, y0, z0],
      [x1, y1, z0],
      [x0, y1, z0],
      [x0, y1, z1],
    ]),
    labelTransform: `matrix(${COS.toFixed(4)} ${SIN} 0 1 ${lx.toFixed(1)} ${ly.toFixed(1)})`,
  };
}

const layerByKey = Object.fromEntries(layers.map((l) => [l.key, l]));

let stackTop = 0;
const blocks = stackPlan.map((plan, index) => {
  const block = { ...layerByKey[plan.key], index, ...buildBlock({ ...plan, z0: stackTop }) };
  stackTop += plan.height;
  return block;
});

const ghostHeight = 52;
const ghost = {
  index: blocks.length,
  ...buildBlock({ dx: 8, dy: -2, z0: stackTop + GHOST_GAP, height: ghostHeight }),
};
const towerHeight = stackTop + GHOST_GAP + ghostHeight;

const shadow = points([
  [-8, -10, 0],
  [LENGTH + 40, -10, 0],
  [LENGTH + 40, DEPTH + 8, 0],
  [-8, DEPTH + 8, 0],
]);
// Slide along x, in the plane of the labelled face, so a pulled block never covers
// the label of the block beneath it.
const pullOffset = iso(PULL, 0, 0);

// viewBox: the footprint's left and right corners set the width, the tallest point and
// the front corner set the height. Pad for the stroke and the pulled-out block.
const pad = 16;
const minX = iso(0, DEPTH + 10, 0)[0] - pad;
const maxX = iso(LENGTH + 40, -10, 0)[0] + pullOffset[0] + pad;
const minY = iso(0, -10, towerHeight)[1] - pad;
const maxY = iso(LENGTH + 40, DEPTH + 8, 0)[1] + pad;
const viewBox = [minX, minY, maxX - minX, maxY - minY].map((n) => n.toFixed(1)).join(' ');

const towerLabel = `A stack of blocks, top to bottom: ${layers.map((l) => l.name).join(', ')}, with an empty block on top for your app.`;

const activeKey = ref(null);
</script>

<template>
  <div class="home mx-auto max-w-6xl pt-6 pb-24 sm:pt-10">
    <!-- hero -->
    <section class="grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,25rem)] lg:gap-16">
      <div class="home__tower mx-auto w-full max-w-[17rem] sm:max-w-xs lg:order-last lg:max-w-none">
        <svg
          class="block w-full overflow-visible"
          :viewBox="viewBox"
          role="img"
          :aria-label="towerLabel"
          :class="{ 'home__tower--drop': shouldDrop }"
        >
          <polygon class="home__shadow" :points="shadow" />
          <g
            v-for="block in blocks"
            :key="block.key"
            class="home__drop"
            :style="{ '--i': block.index }"
            aria-hidden="true"
          >
            <g
              class="home__block"
              :class="{ 'is-active': activeKey === block.key }"
              :style="{
                '--c': block.color,
                '--pull-x': `${pullOffset[0].toFixed(1)}px`,
                '--pull-y': `${pullOffset[1].toFixed(1)}px`,
              }"
            >
              <polygon class="home__face home__face--side" :points="block.side" />
              <polygon class="home__face home__face--top" :points="block.top" />
              <polygon class="home__face home__face--front" :points="block.front" />
              <text
                class="home__label"
                :transform="block.labelTransform"
                :fill="block.labelColor"
                dominant-baseline="central"
              >
                {{ block.name }}
              </text>
            </g>
          </g>
          <g class="home__drop" :style="{ '--i': ghost.index }" aria-hidden="true">
            <g class="home__ghost">
              <polygon class="home__face home__face--ghost home__face--ghost-side" :points="ghost.side" />
              <polygon class="home__face home__face--ghost home__face--ghost-top" :points="ghost.top" />
              <polygon class="home__face home__face--ghost" :points="ghost.front" />
              <text
                class="home__label home__label--ghost"
                :transform="ghost.labelTransform"
                dominant-baseline="central"
              >
                Your app
              </text>
            </g>
          </g>
          <!--
            Hover targets sit on top and never move. If the blocks took the hover themselves,
            a pulled block could slide out from under the pointer and snap back in a loop.
            Drawn bottom first so upper blocks win where silhouettes overlap; the empty block
            is last so it covers the top of the stack without lighting anything up.
          -->
          <g class="home__hits" aria-hidden="true">
            <polygon
              v-for="block in blocks"
              :key="block.key"
              :points="block.outline"
              @mouseenter="activeKey = block.key"
              @mouseleave="activeKey = null"
            />
            <polygon :points="ghost.outline" />
          </g>
        </svg>
      </div>

      <div>
        <h1
          class="home__title max-w-[14ch] text-[2.75rem] font-bold text-gray-900 sm:text-6xl lg:text-[4rem] dark:text-white"
        >
          {{ greeting }}
        </h1>

        <p class="mt-6 max-w-xl text-lg leading-relaxed text-gray-600 sm:text-xl dark:text-gray-300">
          Sign-in, teams, billing, and background jobs already work. Everything here is yours to change.
        </p>

        <div class="mt-8 flex flex-wrap items-center gap-3">
          <a
            :href="docsUrl"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            Read the docs
            <ArrowTopRightOnSquareIcon class="h-4 w-4 opacity-80" aria-hidden="true" />
          </a>
          <a
            v-if="appStore.user?.is_staff"
            href="/admin/"
            class="inline-flex items-center rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            Open Django admin
          </a>
        </div>

        <p class="mt-8 flex items-start gap-2 text-sm text-gray-500 dark:text-gray-400">
          <CodeBracketIcon class="mt-0.5 h-4 w-4 shrink-0 text-gray-400 dark:text-gray-500" aria-hidden="true" />
          <span>
            Replace this page in
            <code
              class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[0.8125rem] text-gray-700 dark:bg-gray-800 dark:text-gray-200"
              >frontend/js/views/HomeView.vue</code
            >
          </span>
        </p>
      </div>
    </section>

    <!-- what's included -->
    <section class="mt-16 lg:mt-14" aria-labelledby="home-included">
      <h2 id="home-included" class="text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
        What's in the box
      </h2>

      <ul class="mt-4">
        <li
          v-for="layer in layers"
          :key="layer.key"
          class="home__row -mx-4 grid items-start gap-x-10 gap-y-2 rounded-2xl px-4 py-5 lg:grid-cols-[15rem_minmax(0,1fr)]"
          :class="{ 'is-active': activeKey === layer.key }"
          :style="{ '--c': layer.color }"
          @mouseenter="activeKey = layer.key"
          @mouseleave="activeKey = null"
        >
          <h3 class="flex items-center gap-3 text-base font-semibold text-gray-900 dark:text-white">
            <span class="home__swatch h-3.5 w-3.5 shrink-0 rounded-[4px]" aria-hidden="true" />
            {{ layer.name }}
          </h3>
          <div>
            <p class="max-w-2xl text-[0.9375rem] leading-relaxed text-gray-600 dark:text-gray-300">
              {{ layer.description }}
            </p>
            <ul class="mt-3 flex flex-wrap gap-1.5" :aria-label="`${layer.name} parts`">
              <li
                v-for="part in layer.parts"
                :key="part"
                class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
              >
                {{ part }}
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.home__title {
  letter-spacing: -0.035em;
  line-height: 1.02;
  text-wrap: balance;
}

/* ---- tower ---- */
.home__shadow {
  fill: rgb(17 24 39 / 0.07);
}
:where([data-theme='dark']) .home__shadow {
  fill: rgb(0 0 0 / 0.35);
}

.home__face {
  stroke: #111827;
  stroke-width: 2;
  stroke-linejoin: round;
}
:where([data-theme='dark']) .home__face {
  stroke: #111827; /* gray-900, the page background, so blocks read as cut-outs */
}
.home__face--front {
  fill: var(--c);
}
.home__face--top {
  fill: color-mix(in oklab, var(--c) 58%, white);
}
.home__face--side {
  fill: color-mix(in oklab, var(--c) 76%, black);
}

.home__label {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.01em;
  pointer-events: none;
  user-select: none;
}

/* Opaque, so the empty block hides what's behind it like the real ones do. */
.home__face--ghost {
  fill: #ffffff;
  stroke: #9ca3af; /* gray-400 */
  stroke-dasharray: 7 6;
  stroke-linecap: round;
}
.home__face--ghost-top {
  fill: #f9fafb; /* gray-50 */
}
.home__face--ghost-side {
  fill: #f3f4f6; /* gray-100 */
}
:where([data-theme='dark']) .home__face--ghost {
  fill: #111827; /* gray-900 */
  stroke: #6b7280; /* gray-500 */
}
:where([data-theme='dark']) .home__face--ghost-top {
  fill: #1f2937; /* gray-800 */
}
:where([data-theme='dark']) .home__face--ghost-side {
  fill: #18212f;
}
.home__label--ghost {
  fill: #6b7280; /* gray-500 */
}
:where([data-theme='dark']) .home__label--ghost {
  fill: #9ca3af; /* gray-400 */
}

.home__hits polygon {
  fill: transparent;
  pointer-events: all;
}

.home__block {
  transition: transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.home__block.is-active {
  transform: translate(var(--pull-x), var(--pull-y));
}

/* ---- list ---- */
.home__swatch {
  background: var(--c);
}
.home__row {
  transition: background-color 200ms ease;
}
.home__row.is-active {
  background: color-mix(in oklab, var(--c) 9%, transparent);
}

/* ---- the one entrance: blocks drop onto the stack, bottom first ---- */
@keyframes homeDrop {
  0% {
    opacity: 0;
    transform: translateY(-140px);
  }
  /* Solid for most of the fall, so you never see the stack through a falling block. */
  18% {
    opacity: 1;
  }
  55% {
    transform: translateY(0);
  }
  72% {
    transform: translateY(-14px);
  }
  86% {
    transform: translateY(0);
  }
  93% {
    transform: translateY(-3px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes homeShadow {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.home__tower--drop .home__drop {
  animation: homeDrop 760ms cubic-bezier(0.33, 0, 0.67, 1) both;
  animation-delay: calc(120ms + var(--i) * 130ms);
}
.home__tower--drop .home__shadow {
  animation: homeShadow 500ms ease-out both;
}

@media (prefers-reduced-motion: reduce) {
  .home__tower--drop .home__drop,
  .home__tower--drop .home__shadow {
    animation: none;
  }
  .home__block,
  .home__row {
    transition: none;
  }
}
</style>
