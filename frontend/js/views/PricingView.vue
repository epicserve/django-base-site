<script setup>
import { computed, inject, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import MarketingLayout from '@/layouts/MarketingLayout.vue';
import BillingCycleToggle from '@/components/billing/BillingCycleToggle.vue';
import PlanCard from '@/components/billing/PlanCard.vue';
import { useBilling } from '@/composables/useBilling';
import { showToast } from '@/composables/useToast';

const appStore = inject('appStore');
const router = useRouter();
const billing = useBilling();
const cycle = ref('monthly');

onMounted(async () => {
  if (!appStore.billing?.enabled) {
    router.replace({ name: 'home' });
    return;
  }
  try {
    await billing.fetchPlans();
  } catch {
    showToast('Could not load plans.', 'error');
  }
  if (appStore.isAuthenticated && appStore.isOrg && appStore.isOwner) {
    try {
      await billing.fetchSubscription();
    } catch {
      // Non-fatal — pricing page still renders.
    }
  }
});

const annualSavings = computed(() => {
  // Pick the highest savings across plans for a "Save up to N%" label.
  let best = 0;
  for (const p of billing.plans.value || []) {
    if (!p.monthly_price_cents || !p.annual_price_cents) continue;
    const yearly = p.monthly_price_cents * 12;
    const pct = Math.round(((yearly - p.annual_price_cents) / yearly) * 100);
    if (pct > best) best = pct;
  }
  return best > 0 ? `Save ${best}%` : '';
});

const currentPlanKey = computed(() => billing.subscription.value?.plan_key || null);
const hasSubscription = computed(() => !!billing.subscription.value?.status);
</script>

<template>
  <MarketingLayout>
    <header class="mx-auto max-w-2xl text-center">
      <h1 class="text-3xl font-semibold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
        Simple, transparent pricing
      </h1>
      <p class="mt-3 text-lg text-gray-500 dark:text-gray-400">
        Pick a plan that fits your team. Switch or cancel anytime.
      </p>
    </header>

    <div class="mt-8 flex justify-center">
      <BillingCycleToggle
        v-model="cycle"
        :annual-savings-label="annualSavings"
      />
    </div>

    <div
      v-if="billing.plansLoading.value && !(billing.plans.value || []).length"
      class="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <div
        v-for="i in 3"
        :key="i"
        class="h-72 animate-pulse rounded-2xl border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-800"
      />
    </div>
    <div
      v-else-if="!(billing.plans.value || []).length"
      class="mt-12 rounded-2xl border border-dashed border-gray-300 p-12 text-center text-gray-500 dark:border-gray-700 dark:text-gray-400"
    >
      <p class="text-lg font-medium">
        No plans configured yet.
      </p>
      <p
        v-if="appStore.user?.is_staff"
        class="mt-1 text-sm"
      >
        Add entries to <code>BILLING_PLANS</code> in your settings to populate this page.
      </p>
      <p
        v-else
        class="mt-1 text-sm"
      >
        Pricing coming soon.
      </p>
    </div>
    <div
      v-else
      class="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <PlanCard
        v-for="plan in billing.plans.value"
        :key="plan.key"
        :plan="plan"
        :features="billing.features.value"
        :billing-cycle="cycle"
        :current-plan-key="currentPlanKey"
        :has-subscription="hasSubscription"
      />
    </div>
  </MarketingLayout>
</template>
