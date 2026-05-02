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
  });

  store.isAuthenticated = computed(() => store.user !== null);
  store.isOrg = computed(() => !!(store.org && store.org.id));
  store.isOwner = computed(() => !!(store.org && store.org.is_owner));

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
