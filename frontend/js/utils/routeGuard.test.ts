import { describe, expect, test } from 'vitest';
import type { RouteMeta } from 'vue-router';
import { initAppStore, type AppStore, type AppUser, type OrgPerm } from '../stores/app';
import { guardRoute, type GuardedRoute } from './routeGuard';

const OWNER_PERMS: OrgPerm[] = ['manage_settings', 'manage_members', 'manage_teams', 'manage_billing'];

function route(name: string, meta: RouteMeta = {}, fullPath = '/somewhere/'): GuardedRoute {
  return { name, meta, params: { slug: 'dunder-mifflin' }, fullPath };
}

function store({
  signedIn = true,
  staff = false,
  superuser = false,
  permissions = OWNER_PERMS as OrgPerm[] | null,
  billing = false,
} = {}): AppStore {
  const appStore = initAppStore();
  appStore.billing.enabled = billing;
  if (signedIn) {
    const user: AppUser = {
      id: 1,
      email: 'michael.scott@dundermifflin.com',
      username: 'michael.scott@dundermifflin.com',
      first_name: 'Michael',
      last_name: 'Scott',
      avatar_url: null,
      impersonation_banner_hidden: false,
      is_hijacked: false,
      is_staff: staff,
      is_superuser: superuser,
      organizations: [],
      timezone: 'America/Chicago',
      timezone_display: 'Central Time (US & Canada)',
    };
    appStore.user = user;
  }
  appStore.org =
    permissions === null
      ? null
      : {
          id: 1,
          name: 'Dunder Mifflin',
          slug: 'dunder-mifflin',
          role: permissions.length > 0 ? 'owner' : 'member',
          permissions,
        };
  return appStore;
}

describe('guardRoute', () => {
  test('sends a signed-out visitor to sign in, then back', () => {
    const to = route('account-general', { requiresAuth: true }, '/accounts/general/?tab=1');

    expect(guardRoute(to, store({ signedIn: false }))).toEqual({
      name: 'login',
      query: { next: '/accounts/general/?tab=1' },
    });
    expect(guardRoute(to, store())).toBe(true);
  });

  test('sends a signed-in user away from guest-only pages', () => {
    const to = route('login', { guest: true });

    expect(guardRoute(to, store())).toEqual({ name: 'home' });
    expect(guardRoute(to, store({ signedIn: false }))).toBe(true);
  });

  test('lets only staff open staff pages', () => {
    const to = route('impersonate', { requiresAuth: true, staffOnly: true });

    expect(guardRoute(to, store())).toEqual({ name: 'home' });
    expect(guardRoute(to, store({ staff: true }))).toBe(true);
  });

  test('lets only superusers open superuser pages', () => {
    const to = route('test-notifications', { requiresAuth: true, superuserOnly: true });

    expect(guardRoute(to, store({ staff: true }))).toEqual({ name: 'home' });
    expect(guardRoute(to, store({ superuser: true }))).toBe(true);
  });

  for (const tab of ['org-settings-general', 'org-settings-members', 'org-settings-teams']) {
    test(`sends a member without permissions home from ${tab}`, () => {
      // The settings APIs need permissions a member lacks; typing the URL used to show "No members." and an invite form.
      const to = route(tab, { requiresAuth: true });

      expect(guardRoute(to, store({ permissions: [] }))).toEqual({ name: 'home' });
      expect(guardRoute(to, store())).toBe(true);
    });
  }

  test('sends someone to the first settings tab their role can open', () => {
    const to = route('org-settings-general', { requiresAuth: true });

    expect(guardRoute(to, store({ permissions: ['manage_teams'] }))).toEqual({
      name: 'org-settings-teams',
      params: { slug: 'dunder-mifflin' },
    });
  });

  test('hides the Billing tab while billing is off', () => {
    const to = route('org-settings-billing', { requiresAuth: true });

    expect(guardRoute(to, store({ billing: false }))).toEqual({
      name: 'org-settings-general',
      params: { slug: 'dunder-mifflin' },
    });
    expect(guardRoute(to, store({ billing: true }))).toBe(true);
  });

  test('hides the pricing page while billing is off', () => {
    const to = route('pricing', { public: true });

    expect(guardRoute(to, store())).toEqual({ name: 'home' });
    expect(guardRoute(to, store({ signedIn: false }))).toEqual({ name: 'login' });
    expect(guardRoute(to, store({ billing: true }))).toBe(true);
  });
});
