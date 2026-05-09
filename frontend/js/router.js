import { createRouter as createVueRouter, createWebHistory } from 'vue-router';

export function createRouter(appStore) {
  const router = createVueRouter({
    history: createWebHistory(),
    routes: [
      // Home
      {
        path: '/',
        name: 'home',
        component: () => import('./views/HomeView.vue'),
        meta: { requiresAuth: true },
      },

      // Organizations
      {
        path: '/organizations/invite/:key/accept/',
        name: 'accept-invite',
        component: () => import('./views/AcceptInviteView.vue'),
      },
      {
        path: '/organizations/switch/',
        name: 'org-switch',
        component: () => import('./views/OrgSwitchView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/organizations/create/',
        name: 'org-create',
        component: () => import('./views/OrgCreateView.vue'),
        meta: { requiresAuth: true },
      },

      // Organization Settings (nested tabs)
      {
        path: '/organizations/:slug/settings/',
        component: () => import('./layouts/OrgSettingsLayout.vue'),
        meta: { requiresAuth: true },
        children: [
          { path: '', redirect: (to) => ({ name: 'org-settings-general', params: to.params }) },
          {
            path: 'general/',
            name: 'org-settings-general',
            component: () => import('./views/settings/GeneralView.vue'),
          },
          {
            path: 'members/',
            name: 'org-settings-members',
            component: () => import('./views/settings/MembersView.vue'),
          },
          {
            path: 'teams/',
            name: 'org-settings-teams',
            component: () => import('./views/settings/TeamsView.vue'),
          },
        ],
      },

      // Auth / Accounts
      {
        path: '/accounts/login/',
        name: 'login',
        component: () => import('./accounts/views/LoginView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/signup/',
        name: 'signup',
        component: () => import('./accounts/views/SignupView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/password/reset/',
        name: 'password-reset',
        component: () => import('./accounts/views/PasswordResetView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/password/reset/done/',
        name: 'password-reset-done',
        component: () => import('./accounts/views/PasswordResetDoneView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/password/reset/key/:key/',
        name: 'password-reset-key',
        component: () => import('./accounts/views/PasswordResetKeyView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/password/reset/key/done/',
        name: 'password-reset-key-done',
        component: () => import('./accounts/views/PasswordResetKeyDoneView.vue'),
        meta: { guest: true },
      },
      {
        path: '/accounts/confirm-email/:key/',
        name: 'confirm-email',
        component: () => import('./accounts/views/EmailConfirmView.vue'),
      },
      {
        path: '/accounts/verification-sent/',
        name: 'verification-sent',
        component: () => import('./accounts/views/VerificationSentView.vue'),
      },
      {
        path: '/accounts/logout/',
        name: 'logout',
        component: () => import('./accounts/views/LogoutView.vue'),
      },
      {
        path: '/accounts/general/',
        name: 'account-general',
        component: () => import('./accounts/views/AccountGeneralView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/email/',
        name: 'account-email',
        component: () => import('./accounts/views/AccountEmailView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/password/change/',
        name: 'account-password-change',
        component: () => import('./accounts/views/AccountPasswordChangeView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/security/',
        name: 'account-security',
        component: () => import('./accounts/views/AccountSecurityView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/notifications/',
        name: 'account-notifications',
        component: () => import('./accounts/views/AccountNotificationsView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/security/totp/',
        name: 'account-totp',
        component: () => import('./accounts/views/AccountTotpView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/security/recovery-codes/',
        name: 'account-recovery-codes',
        component: () => import('./accounts/views/AccountRecoveryCodesView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/security/passkeys/',
        name: 'account-passkeys',
        component: () => import('./accounts/views/AccountPasskeysView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/accounts/2fa/',
        name: 'two-factor',
        component: () => import('./accounts/views/TwoFactorView.vue'),
      },
      {
        path: '/accounts/reauthenticate/',
        name: 'account-reauthenticate',
        component: () => import('./accounts/views/ReauthenticateView.vue'),
        meta: { requiresAuth: true },
      },

      // Impersonation (staff only)
      {
        path: '/impersonate/',
        name: 'impersonate',
        component: () => import('./views/ImpersonateSearchView.vue'),
        meta: { requiresAuth: true, staffOnly: true },
      },

      // Test notifications (superuser only)
      {
        path: '/test-notifications/',
        name: 'test-notifications',
        component: () => import('./views/TestNotificationsView.vue'),
        meta: { requiresAuth: true, superuserOnly: true },
      },

      // 404 catch-all
      {
        path: '/:pathMatch(.*)*',
        name: 'not-found',
        component: () => import('./views/NotFoundView.vue'),
      },
    ],
  });

  router.beforeEach(async (to) => {
    if (appStore.contextReady) await appStore.contextReady;
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
    return true;
  });

  router.onError((err, to) => {
    const msg = err?.message ?? '',
     isChunkError =
      err?.name === 'ChunkLoadError' ||
      /Loading chunk \S+ failed/i.test(msg) ||
      /Failed to fetch dynamically imported module/i.test(msg) ||
      /Importing a module script failed/i.test(msg);
    if (isChunkError && to?.fullPath) {
      window.location.assign(to.fullPath);
    }
  });

  return router;
}
