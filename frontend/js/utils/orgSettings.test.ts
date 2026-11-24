import { describe, expect, test } from 'bun:test';
import { initAppStore, type AppStore, type OrgPerm } from '../stores/app';
import { isOrgSettingsTab, orgSettingsTabs } from './orgSettings';

const ALL_PERMS: OrgPerm[] = ['manage_settings', 'manage_members', 'manage_teams', 'manage_billing'];

function makeStore(permissions: OrgPerm[] | null, billingEnabled = false): AppStore {
  const appStore = initAppStore();

  appStore.billing.enabled = billingEnabled;
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

describe('isOrgSettingsTab', () => {
  for (const name of ['org-settings-general', 'org-settings-members', 'org-settings-teams', 'org-settings-billing']) {
    test(`recognizes ${name}`, () => {
      expect(isOrgSettingsTab(name)).toBe(true);
    });
  }

  for (const name of ['home', 'org-switch', 'pricing', '', undefined, null, 42]) {
    test(`rejects ${JSON.stringify(name)}`, () => {
      expect(isOrgSettingsTab(name)).toBe(false);
    });
  }
});

describe('orgSettingsTabs', () => {
  test('returns general, members, and teams for all perms when billing is off', () => {
    const names = orgSettingsTabs(makeStore(ALL_PERMS, false)).map((tab) => tab.name);

    expect(names).toEqual(['org-settings-general', 'org-settings-members', 'org-settings-teams']);
  });

  test('includes billing for all perms when billing is on', () => {
    const names = orgSettingsTabs(makeStore(ALL_PERMS, true)).map((tab) => tab.name);

    expect(names).toEqual([
      'org-settings-general',
      'org-settings-members',
      'org-settings-teams',
      'org-settings-billing',
    ]);
  });

  test('returns only the tab matching a single permission', () => {
    expect(orgSettingsTabs(makeStore(['manage_members'], true)).map((tab) => tab.name)).toEqual([
      'org-settings-members',
    ]);
    expect(orgSettingsTabs(makeStore(['manage_billing'], true)).map((tab) => tab.name)).toEqual([
      'org-settings-billing',
    ]);
    expect(orgSettingsTabs(makeStore(['manage_billing'], false))).toEqual([]);
  });

  test('returns no tabs when the role has no permissions', () => {
    expect(orgSettingsTabs(makeStore([], false))).toEqual([]);
    expect(orgSettingsTabs(makeStore([], true))).toEqual([]);
  });

  test('returns no tabs when there is no current organization', () => {
    expect(orgSettingsTabs(makeStore(null, false))).toEqual([]);
    expect(orgSettingsTabs(makeStore(null, true))).toEqual([]);
  });
});
