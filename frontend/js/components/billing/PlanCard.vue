<script setup>
import { computed, inject, ref } from 'vue';
import { useRouter } from 'vue-router';
import { CheckIcon } from '@heroicons/vue/20/solid';
import { useBilling } from '@/composables/useBilling';
import { showToast } from '@/composables/useToast';

const props = defineProps({
  plan: { type: Object, required: true },
  features: { type: Array, default: () => [] },
  billingCycle: { type: String, required: true },
  currentPlanKey: { type: String, default: null },
  hasSubscription: { type: Boolean, default: false },
});

const appStore = inject('appStore');
const router = useRouter();
const billing = useBilling();
const busy = ref(false);

const priceCents = computed(() =>
  props.billingCycle === 'annual' ? props.plan.annual_price_cents : props.plan.monthly_price_cents,
);

const priceLabel = computed(() => {
  if (props.plan.is_free) return 'Free';
  if (!priceCents.value) return '—';
  const fmt = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: (props.plan.currency || 'usd').toUpperCase(),
    minimumFractionDigits: 0,
  });
  return fmt.format(priceCents.value / 100);
});

const cycleSuffix = computed(() => {
  if (props.plan.is_free || !priceCents.value) return '';
  return props.billingCycle === 'annual' ? '/yr' : '/mo';
});

const annualSavingsPct = computed(() => {
  const monthly = props.plan.monthly_price_cents;
  const annual = props.plan.annual_price_cents;
  if (!monthly || !annual) return 0;
  const yearlyAtMonthly = monthly * 12;
  return Math.round(((yearlyAtMonthly - annual) / yearlyAtMonthly) * 100);
});

const ctaState = computed(() => {
  if (!appStore.isAuthenticated) {
    return {
      label: props.plan.is_free ? 'Get started' : 'Sign up',
      action: () => router.push({ name: 'signup', query: { next: '/pricing/' } }),
      disabled: false,
      hint: '',
    };
  }
  if (!appStore.isOrg) {
    return {
      label: 'Create an organization',
      action: () => router.push({ name: 'org-create' }),
      disabled: false,
      hint: '',
    };
  }
  if (!appStore.isOwner) {
    return {
      label: 'Owner-only',
      action: null,
      disabled: true,
      hint: 'Only org owners can change billing.',
    };
  }
  if (props.currentPlanKey && props.currentPlanKey === props.plan.key) {
    return { label: 'Current plan', action: null, disabled: true, hint: '' };
  }
  if (props.hasSubscription) {
    // Switching plans (upgrade or downgrade) goes through Stripe Customer Portal.
    return {
      label: props.plan.is_free ? 'Downgrade to Free' : 'Switch to this plan',
      action: () => billing.manageBilling(),
      disabled: false,
      hint: '',
    };
  }
  if (props.plan.is_free) {
    return { label: 'Use free plan', action: null, disabled: true, hint: 'You\'re already on the free plan.' };
  }
  return {
    label: 'Subscribe',
    action: () => billing.subscribe(props.plan.key, props.billingCycle),
    disabled: false,
    hint: '',
  };
});

async function onClick() {
  if (busy.value || ctaState.value.disabled || !ctaState.value.action) return;
  busy.value = true;
  try {
    await ctaState.value.action();
  } catch (err) {
    showToast(err?.data?.detail || 'Something went wrong. Please try again.', 'error');
  } finally {
    busy.value = false;
  }
}

const featureRows = computed(() => {
  if (!props.features || props.features.length === 0) {
    return Object.entries(props.plan.features || {}).map(([key, value]) => ({
      key,
      label: key,
      value,
      type: typeof value === 'boolean' ? 'bool' : 'limit',
    }));
  }
  return props.features.map((f) => ({
    key: f.key,
    label: f.label || f.key,
    description: f.description,
    type: f.type,
    value: props.plan.features?.[f.key] ?? f.default,
  }));
});

function describeFeature(row) {
  if (row.type === 'bool') return row.label;
  return `${row.value} ${row.label.toLowerCase()}`;
}

function showCheck(row) {
  if (row.type === 'bool') return Boolean(row.value);
  if (typeof row.value === 'number') return row.value > 0;
  return row.value != null;
}
</script>

<template>
  <article
    class="flex flex-col gap-5 rounded-2xl border bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
    :class="plan.is_highlighted ? 'border-indigo-500 ring-2 ring-indigo-500' : 'border-gray-200'"
  >
    <header class="flex flex-col gap-1">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ plan.name }}
        </h3>
        <span
          v-if="plan.is_highlighted"
          class="inline-flex items-center rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"
        >
          Popular
        </span>
      </div>
      <p
        v-if="plan.description"
        class="text-sm text-gray-500 dark:text-gray-400"
      >
        {{ plan.description }}
      </p>
    </header>

    <div class="flex items-baseline gap-1">
      <span class="text-3xl font-semibold text-gray-900 dark:text-white">{{ priceLabel }}</span>
      <span
        v-if="cycleSuffix"
        class="text-sm text-gray-500 dark:text-gray-400"
      >
        {{ cycleSuffix }}
      </span>
    </div>
    <p
      v-if="billingCycle === 'annual' && annualSavingsPct > 0 && !plan.is_free"
      class="text-xs font-medium text-green-600 dark:text-green-400"
    >
      Save {{ annualSavingsPct }}% with annual billing
    </p>
    <p
      v-if="plan.trial_days > 0 && !hasSubscription"
      class="text-xs text-gray-500 dark:text-gray-400"
    >
      {{ plan.trial_days }}-day free trial
    </p>

    <ul class="flex-1 space-y-2 text-sm text-gray-700 dark:text-gray-300">
      <li
        v-for="row in featureRows"
        :key="row.key"
        class="flex items-start gap-2"
      >
        <CheckIcon
          class="mt-0.5 h-4 w-4 shrink-0"
          :class="showCheck(row) ? 'text-green-600 dark:text-green-400' : 'text-gray-300 dark:text-gray-600'"
        />
        <span :class="showCheck(row) ? '' : 'text-gray-400 line-through dark:text-gray-500'">
          {{ describeFeature(row) }}
        </span>
      </li>
    </ul>

    <button
      type="button"
      class="rounded-md px-4 py-2 text-sm font-medium transition"
      :class="ctaState.disabled
        ? 'cursor-not-allowed bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500'
        : 'cursor-pointer bg-indigo-600 text-white hover:bg-indigo-500'"
      :disabled="ctaState.disabled || busy"
      :aria-disabled="ctaState.disabled"
      :title="ctaState.hint || undefined"
      @click="onClick"
    >
      <span v-if="busy">…</span>
      <span v-else>{{ ctaState.label }}</span>
    </button>
  </article>
</template>
