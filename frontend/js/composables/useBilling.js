import { ref } from 'vue';
import { get, post } from '@/utils/api';

const subscription = ref(null),
 plans = ref([]),
 features = ref([]),
 subscriptionLoading = ref(false),
 plansLoading = ref(false);

let pollHandle = null;

async function fetchSubscription() {
  subscriptionLoading.value = true;
  try {
    subscription.value = await get('/api/billing/subscription/');
  } finally {
    subscriptionLoading.value = false;
  }
}

async function fetchPlans() {
  plansLoading.value = true;
  try {
    const [planList, featureList] = await Promise.all([get('/api/billing/plans/'), get('/api/billing/features/')]);
    plans.value = planList;
    features.value = featureList;
  } finally {
    plansLoading.value = false;
  }
}

async function subscribe(planKey, billingCycle) {
  // Full-page redirect — Stripe-recommended for hosted Checkout. New tabs / popups
  // are blocked by Safari and confuse password managers.
  const { checkout_url } = await post('/api/billing/checkout/', {
    plan_key: planKey,
    billing_cycle: billingCycle,
  });
  window.location.href = checkout_url;
}

async function manageBilling() {
  const { portal_url } = await post('/api/billing/portal/');
  window.location.href = portal_url;
}

async function pollUntilActive({ timeoutMs = 30000, intervalMs = 2000 } = {}) {
  const start = Date.now();
  return new Promise((resolve) => {
    const tick = async () => {
      try {
        await fetchSubscription();
      } catch {
        // keep trying
      }
      const s = subscription.value,
       ready = s && s.status && ['trialing', 'active'].includes(s.status);
      if (ready || Date.now() - start > timeoutMs) {
        resolve(!!ready);
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
