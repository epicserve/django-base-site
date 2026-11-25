import type { RouteLocationNormalized, RouteLocationRaw } from 'vue-router';
import type { AppStore } from '@/stores/app';
import { isOrgSettingsTab, orgSettingsTabs } from '@/utils/orgSettings';

export type GuardedRoute = Pick<RouteLocationNormalized, 'name' | 'meta' | 'params' | 'fullPath'>;

/**
 * Where the router sends a navigation to `to`, or `true` to let it through. The router's `beforeEach` calls it once the
 * app context has loaded, so `appStore` knows who is signed in and what they may open.
 */
export function guardRoute(to: GuardedRoute, appStore: AppStore): RouteLocationRaw | true {
  if (to.meta.requiresAuth && !appStore.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } };
  }
  if (to.meta.guest && appStore.isAuthenticated) {
    return { name: 'home' };
  }
  if (to.meta.staffOnly && !appStore.user?.is_staff) {
    return { name: 'home' };
  }
  if (to.meta.superuserOnly && !appStore.user?.is_superuser) {
    return { name: 'home' };
  }
  if (isOrgSettingsTab(to.name)) {
    // Also hides the Billing tab when BILLING_ENABLED is false.
    const tabs = orgSettingsTabs(appStore);
    if (!tabs.some((tab) => tab.name === to.name)) {
      return tabs[0] ? { name: tabs[0].name, params: to.params } : { name: 'home' };
    }
  }
  // When BILLING_ENABLED is false, hide the pricing page so users don't land on a dead route.
  if (to.name === 'pricing' && !appStore.billing.enabled) {
    return appStore.isAuthenticated ? { name: 'home' } : { name: 'login' };
  }
  return true;
}
