<script setup>
import { computed, inject, onMounted, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { useBilling } from '@/composables/useBilling';
import { showToast } from '@/composables/useToast';
import SubscriptionStatusBadge from '@/components/billing/SubscriptionStatusBadge.vue';

const appStore = inject('appStore');
const route = useRoute();
const router = useRouter();
const billing = useBilling();
const activating = ref(false);
const portalBusy = ref(false);

onMounted(async () => {
  if (!appStore.isOwner) return;
  await billing.fetchSubscription();
  if (route.query.checkout === 'success') {
    activating.value = true;
    showToast('Welcome! Activating your plan…', 'success');
    const ok = await billing.pollUntilActive();
    activating.value = false;
    if (ok) {
      showToast('Your subscription is active.', 'success');
      await appStore.fetchContext();
    } else {
      showToast('Your subscription should appear shortly. Refresh if it doesn\'t.', 'error');
    }
    router.replace({ name: route.name, params: route.params, query: {} });
  } else if (route.query.portal === 'return') {
    await appStore.fetchContext();
    router.replace({ name: route.name, params: route.params, query: {} });
  }
});

const sub = computed(() => billing.subscription.value);
const hasSubscription = computed(() => !!sub.value?.status);
const trialDaysLeft = computed(() => {
  if (!sub.value?.trial_end) return null;
  const ms = new Date(sub.value.trial_end).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
});
const periodEndLabel = computed(() => {
  if (!sub.value?.current_period_end) return null;
  return new Date(sub.value.current_period_end).toLocaleDateString();
});

async function onManageBilling() {
  if (portalBusy.value) return;
  portalBusy.value = true;
  try {
    await billing.manageBilling();
  } catch (err) {
    showToast(err?.data?.detail || 'Could not open the billing portal.', 'error');
  } finally {
    portalBusy.value = false;
  }
}
</script>

<template>
  <div class="space-y-6">
    <div
      v-if="!appStore.isOwner"
      class="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-center text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
    >
      Only org owners can manage billing. Contact your owner to make changes.
    </div>

    <template v-else>
      <!-- Past-due warning -->
      <div
        v-if="sub?.status === 'past_due' || sub?.status === 'unpaid'"
        class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-700/50 dark:bg-red-900/20 dark:text-red-300"
      >
        <p class="font-medium">
          Your last payment failed.
        </p>
        <p class="mt-1">
          Update your payment method to keep your subscription active.
        </p>
        <button
          type="button"
          class="mt-3 cursor-pointer rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500"
          :disabled="portalBusy"
          @click="onManageBilling"
        >
          Update payment method
        </button>
      </div>

      <!-- Activating spinner -->
      <div
        v-if="activating"
        class="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
      >
        <svg
          class="h-5 w-5 animate-spin text-indigo-600"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          />
        </svg>
        <span class="text-sm text-gray-600 dark:text-gray-300">Activating your plan…</span>
      </div>

      <!-- Loading skeleton -->
      <div
        v-else-if="billing.subscriptionLoading.value && !sub"
        class="space-y-4"
      >
        <div class="h-32 animate-pulse rounded-lg border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-700" />
        <div class="h-24 animate-pulse rounded-lg border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-700" />
      </div>

      <!-- No subscription -->
      <div
        v-else-if="!hasSubscription"
        class="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
      >
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
          No active subscription
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Choose a plan to upgrade your organization.
        </p>
        <RouterLink
          :to="{ name: 'pricing' }"
          class="mt-4 inline-flex cursor-pointer rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          View plans
        </RouterLink>
      </div>

      <!-- Active subscription -->
      <template v-else>
        <section class="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <header class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
              Current plan
            </h2>
            <SubscriptionStatusBadge :status="sub.status" />
          </header>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
            <span class="font-medium">{{ sub.plan?.name || sub.plan_key }}</span>
            <span
              v-if="sub.billing_cycle"
              class="text-gray-500 dark:text-gray-400"
            >
              · billed {{ sub.billing_cycle }}
            </span>
          </p>
          <p
            v-if="sub.status === 'trialing' && trialDaysLeft !== null"
            class="mt-2 text-sm text-blue-700 dark:text-blue-300"
          >
            Trial ends in {{ trialDaysLeft }} {{ trialDaysLeft === 1 ? 'day' : 'days' }}.
          </p>
          <p
            v-if="sub.cancel_at_period_end && periodEndLabel"
            class="mt-2 text-sm text-amber-700 dark:text-amber-300"
          >
            Your plan ends on {{ periodEndLabel }}.
          </p>
          <p
            v-else-if="periodEndLabel && (sub.status === 'active' || sub.status === 'trialing')"
            class="mt-2 text-sm text-gray-500 dark:text-gray-400"
          >
            Renews on {{ periodEndLabel }}.
          </p>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Manage billing
          </h2>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Open the Stripe billing portal to update payment methods,
            cancel your subscription, or download invoices.
          </p>
          <button
            type="button"
            class="mt-4 cursor-pointer rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="portalBusy"
            @click="onManageBilling"
          >
            <span v-if="portalBusy">Opening…</span>
            <span v-else>Open billing portal</span>
          </button>
        </section>

        <section
          v-if="sub.quantity && sub.quantity > 1"
          class="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
        >
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Seats
          </h2>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ sub.quantity }} seats. Adjusting members updates your subscription automatically.
          </p>
          <RouterLink
            :to="{ name: 'org-settings-members' }"
            class="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Manage members →
          </RouterLink>
        </section>
      </template>
    </template>
  </div>
</template>
