import type { AppStore, OrgPerm } from '@/stores/app';

/** The organization settings tabs, in order, each with the permission it takes to open it. */
const TABS = [
  { name: 'org-settings-general', label: 'General', perm: 'manage_settings' },
  { name: 'org-settings-members', label: 'Members', perm: 'manage_members' },
  { name: 'org-settings-teams', label: 'Teams', perm: 'manage_teams' },
  { name: 'org-settings-billing', label: 'Billing', perm: 'manage_billing' },
] as const satisfies readonly { name: string; label: string; perm: OrgPerm }[];

export type OrgSettingsTab = (typeof TABS)[number];

const TAB_NAMES: ReadonlySet<unknown> = new Set(TABS.map((tab) => tab.name));

export function isOrgSettingsTab(routeName: unknown): boolean {
  return TAB_NAMES.has(routeName);
}

/** The tabs the user can open: their role grants the tab's permission, and Billing only when billing is on. */
export function orgSettingsTabs(appStore: AppStore): OrgSettingsTab[] {
  return TABS.filter(
    (tab) => appStore.can(tab.perm) && (tab.name !== 'org-settings-billing' || appStore.billing.enabled),
  );
}
