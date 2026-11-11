import { computed, reactive, type ComputedRef } from 'vue';
import type { components } from '@/api/schema';
import { api, unwrap } from '@/utils/api';

type Schemas = components['schemas'];
export type AppUser = Schemas['AppUserOut'];
export type CurrentOrg = Schemas['OrgSelectOut'];
export type OrgSummary = Schemas['OrgSummaryOut'];
export type BillingSummary = Schemas['BillingSummaryOut'];
export type FeatureValue = BillingSummary['features'][string];

export interface AppStore {
  user: AppUser | null;
  org: CurrentOrg | null;
  organizations: OrgSummary[];
  orgMemberCount: number;
  orgOwnerCount: number;
  siteName: string;
  instance: string;
  debug: boolean;
  signupOpen: boolean;
  loading: boolean;
  version: string | null;
  updateAvailable: boolean;
  billing: BillingSummary;
  readonly isAuthenticated: boolean;
  readonly isOrg: boolean;
  readonly isOwner: boolean;
  hasFeature(key: string): boolean;
  featureValue<Fallback = null>(key: string, fallback?: Fallback | null): FeatureValue | Fallback;
  fetchContext(): Promise<void>;
  setUser(user: AppUser | null): void;
  clearUser(): void;
  switchOrg(slug: string): Promise<void>;
  signOutOrg(): Promise<void>;
}

type Computed = 'isAuthenticated' | 'isOrg' | 'isOwner';

// What's passed to reactive(), which unwraps the computed refs into the plain booleans `AppStore` declares.
type AppStoreSource = Omit<AppStore, Computed> & { [Key in Computed]: ComputedRef<boolean> };

let store: AppStore | null = null;

export function initAppStore(): AppStore {
  let inFlightContext: Promise<void> | null = null;

  const appStore: AppStore = reactive<AppStoreSource>({
    user: null,
    org: null,
    organizations: [],
    orgMemberCount: 0,
    orgOwnerCount: 0,
    siteName: '',
    instance: '',
    debug: false,
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

    isAuthenticated: computed(() => appStore.user !== null),
    isOrg: computed(() => !!appStore.org?.id),
    isOwner: computed(() => !!appStore.org?.is_owner),

    // Feature gating helpers. When billing is disabled, hasFeature returns true
    // so downstream gates pass and the starter template "just works" without
    // Stripe credentials. featureValue still returns the caller-provided fallback
    // since "unlimited" semantics depend on the caller (e.g. Infinity for limits).
    hasFeature(key: string) {
      if (!appStore.billing.enabled) return true;
      const v = appStore.billing.features[key];
      if (typeof v === 'boolean') return v;
      if (typeof v === 'number') return v > 0;
      return v != null && v !== '';
    },
    featureValue<Fallback = null>(key: string, fallback: Fallback | null = null) {
      if (!appStore.billing.enabled) return fallback;
      const v = appStore.billing.features[key];
      return v == null ? fallback : v;
    },

    fetchContext() {
      if (inFlightContext) return inFlightContext;
      inFlightContext = (async () => {
        try {
          const data = await unwrap(api.GET('/api/app-context/'));
          appStore.user = data.user;
          appStore.org = data.org;
          appStore.organizations = data.organizations;
          appStore.orgMemberCount = data.orgMemberCount;
          appStore.orgOwnerCount = data.orgOwnerCount;
          appStore.siteName = data.siteName;
          appStore.instance = data.instance;
          appStore.debug = data.debug;
          appStore.signupOpen = data.signupOpen;
          appStore.billing = data.billing;
          if (appStore.version === null) {
            appStore.version = data.version;
          } else if (data.version && data.version !== appStore.version) {
            appStore.updateAvailable = true;
          }
          appStore.loading = false;
        } finally {
          inFlightContext = null;
        }
      })();
      return inFlightContext;
    },

    setUser(user: AppUser | null) {
      appStore.user = user;
    },

    clearUser() {
      appStore.user = null;
      appStore.org = null;
      appStore.organizations = [];
    },

    async switchOrg(slug: string) {
      appStore.org = await unwrap(api.POST('/api/organizations/{slug}/select/', { params: { path: { slug } } }));
      await appStore.fetchContext();
    },

    async signOutOrg() {
      await unwrap(api.POST('/api/organizations/signout/'));
      appStore.org = null;
      await appStore.fetchContext();
    },
  });

  store = appStore;
  return appStore;
}

/** The store `initAppStore()` created. Components can also `inject('appStore')`, which returns the same object. */
export function useAppStore(): AppStore {
  if (store === null) throw new Error('initAppStore() has not been called.');
  return store;
}
