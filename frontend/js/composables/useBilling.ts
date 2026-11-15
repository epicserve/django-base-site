import { ref } from 'vue';
import type { components } from '@/api/schema';
import { api, unwrap } from '@/utils/api';

type Schemas = components['schemas'];
export type Subscription = Schemas['SubscriptionOut'];
export type Plan = Schemas['PlanOut'];
export type Feature = Schemas['FeatureOut'];
export type BillingCycle = Schemas['CheckoutIn']['billing_cycle'];

const subscription = ref<Subscription | null>(null),
  plans = ref<Plan[]>([]),
  features = ref<Feature[]>([]),
  subscriptionLoading = ref(false),
  plansLoading = ref(false);

let pollHandle: ReturnType<typeof setTimeout> | null = null;

async function fetchSubscription() {
  subscriptionLoading.value = true;
  try {
    subscription.value = await unwrap(api.GET('/api/billing/subscription/'));
  } finally {
    subscriptionLoading.value = false;
  }
}

async function fetchPlans() {
  plansLoading.value = true;
  try {
    const [planList, featureList] = await Promise.all([
      unwrap(api.GET('/api/billing/plans/')),
      unwrap(api.GET('/api/billing/features/')),
    ]);
    plans.value = planList;
    features.value = featureList;
  } finally {
    plansLoading.value = false;
  }
}

async function subscribe(planKey: string, billingCycle: BillingCycle) {
  // Full-page redirect — Stripe-recommended for hosted Checkout. New tabs / popups
  // are blocked by Safari and confuse password managers.
  const { checkout_url } = await unwrap(
    api.POST('/api/billing/checkout/', { body: { plan_key: planKey, billing_cycle: billingCycle } }),
  );
  window.location.href = checkout_url;
}

async function manageBilling() {
  const { portal_url } = await unwrap(api.POST('/api/billing/portal/'));
  window.location.href = portal_url;
}

async function pollUntilActive({ timeoutMs = 30000, intervalMs = 2000 } = {}): Promise<boolean> {
  const start = Date.now();
  return new Promise((resolve) => {
    const tick = async () => {
      try {
        await fetchSubscription();
      } catch {
        // keep trying
      }
      const status = subscription.value?.status,
        ready = !!status && ['trialing', 'active'].includes(status);
      if (ready || Date.now() - start > timeoutMs) {
        resolve(ready);
        return;
      }
      pollHandle = setTimeout(tick, intervalMs);
    };
    tick();
  });
}

function cancelPolling() {
  if (pollHandle) {
    clearTimeout(pollHandle);
    pollHandle = null;
  }
}

export function useBilling() {
  return {
    subscription,
    plans,
    features,
    subscriptionLoading,
    plansLoading,
    fetchSubscription,
    fetchPlans,
    subscribe,
    manageBilling,
    pollUntilActive,
    cancelPolling,
  };
}
