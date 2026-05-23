import { computed, reactive } from 'vue';
import { get, post } from '@/utils/api';

let store = null;

export function initAppStore() {
  store = reactive({
    user: null,
    org: null,
    organizations: [],
    orgMemberCount: 0,
    orgOwnerCount: 0,
    siteName: '',
    instance: '',
    signupOpen: true,
    loading: true,
    version: null,
    updateAvailable: false,
    billing: {
      enabled: false,
      publishable_key: '',
      plan: null,
      status: null,
      billing_cycle: null,
      trial_end: null,
      cancel_at_period_end: false,
      features: {},
    },
  });

  store.isAuthenticated = computed(() => store.user !== null);
  store.isOrg = computed(() => !!(store.org && store.org.id));
  store.isOwner = computed(() => !!(store.org && store.org.is_owner));

  // Feature gating helpers. When billing is disabled, hasFeature returns true
  // so downstream gates pass and the starter template "just works" without
  // Stripe credentials. featureValue still returns the caller-provided fallback
  // since "unlimited" semantics depend on the caller (e.g. Infinity for limits).
  store.hasFeature = (key) => {
    if (!store.billing?.enabled) return true;
    const v = store.billing.features?.[key];
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v > 0;
    return v != null && v !== '';
  };
  store.featureValue = (key, fallback = null) => {
    if (!store.billing?.enabled) return fallback;
    const v = store.billing.features?.[key];
    return v == null ? fallback : v;
  };

  let inFlightContext = null;
  store.fetchContext = () => {
    if (inFlightContext) return inFlightContext;
    inFlightContext = (async () => {
      try {
        const data = await get('/api/app-context/');
        store.user = data.user;
        store.org = data.org;
        store.organizations = data.organizations;
        store.orgMemberCount = data.orgMemberCount;
        store.orgOwnerCount = data.orgOwnerCount;
        store.siteName = data.siteName;
        store.instance = data.instance;
        store.signupOpen = data.signupOpen;
        if (data.billing) {
          store.billing = {
            enabled: !!data.billing.enabled,
            publishable_key: data.billing.publishable_key || '',
            plan: data.billing.plan || null,
            status: data.billing.status || null,
            billing_cycle: data.billing.billing_cycle || null,
            trial_end: data.billing.trial_end || null,
            cancel_at_period_end: !!data.billing.cancel_at_period_end,
            features: data.billing.features || {},
          };
        }
        if (store.version === null) {
          store.version = data.version;
        } else if (data.version && data.version !== store.version) {
          store.updateAvailable = true;
        }
        store.loading = false;
      } finally {
        inFlightContext = null;
      }
    })();
    return inFlightContext;
  };

  store.setUser = (user) => {
    store.user = user;
  };

  store.clearUser = () => {
    store.user = null;
    store.org = null;
    store.organizations = [];
  };

  store.switchOrg = async (slug) => {
    const data = await post(`/api/organizations/${slug}/select/`);
    store.org = data;
    await store.fetchContext();
  };

  store.signOutOrg = async () => {
    await post('/api/organizations/signout/');
    store.org = null;
    await store.fetchContext();
  };

  return store;
}

export function useAppStore() {
  return store;
}
