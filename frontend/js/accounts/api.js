import { get, post, del, request } from '../utils/api';

export function parseAllauthErrors(responseData) {
  const errors = {};

  if (responseData?.errors) {
    for (const err of responseData.errors) {
      const key = err.param || 'non_field_errors';

      if (!errors[key]) errors[key] = [];
      errors[key].push(err.message);
    }
  }
  if (Object.keys(errors).length === 0) {
    return { non_field_errors: ['An unexpected error occurred.'] };
  }
  return errors;
}

const BASE = '/_allauth/browser/v1',

  authApi = {
    getSession: () => get(`${BASE}/auth/session`),

    login: (email, password) => post(`${BASE}/auth/login`, { email, password }),

    logout: () => del(`${BASE}/auth/session`),

    signup: (data) => post(`${BASE}/auth/signup`, data),

    requestPasswordReset: (email) => post(`${BASE}/auth/password/request`, { email }),

    resetPassword: (key, password) => post(`${BASE}/auth/password/reset`, { key, password }),

    changePassword: (data) => post(`${BASE}/account/password/change`, data),

    verifyEmail: (key) => post(`${BASE}/auth/email/verify`, { key }),

    listEmails: () => get(`${BASE}/account/email`),

    addEmail: (email) => post(`${BASE}/account/email`, { email }),

    setPrimaryEmail: (email) => request(`${BASE}/account/email`, {
      method: 'PUT',
      body: JSON.stringify({ email, primary: true }),
    }),

    removeEmail: (email) => request(`${BASE}/account/email`, {
      method: 'DELETE',
      body: JSON.stringify({ email }),
    }),

    resendVerification: (email) => request(`${BASE}/account/email`, {
      method: 'PUT',
      body: JSON.stringify({ email }),
    }),

    // MFA / 2FA
    listAuthenticators: () => get(`${BASE}/account/authenticators`),

    getTotpStatus: () => get(`${BASE}/account/authenticators/totp`),

    activateTotp: (code) => post(`${BASE}/account/authenticators/totp`, { code }),

    deactivateTotp: () => del(`${BASE}/account/authenticators/totp`),

    listRecoveryCodes: () => get(`${BASE}/account/authenticators/recovery-codes`),

    regenerateRecoveryCodes: () => post(`${BASE}/account/authenticators/recovery-codes`, {}),

    beginAddPasskey: (passwordless) => get(
      `${BASE}/account/authenticators/webauthn`,
      { passwordless: passwordless ? 'true' : 'false' },
    ),

    addPasskey: (name, credential) => post(`${BASE}/account/authenticators/webauthn`, {
      name,
      credential,
    }),

    renamePasskey: (id, name) => request(`${BASE}/account/authenticators/webauthn`, {
      method: 'PUT',
      body: JSON.stringify({ id, name }),
    }),

    removePasskey: (id) => request(`${BASE}/account/authenticators/webauthn`, {
      method: 'DELETE',
      body: JSON.stringify({ authenticators: [id] }),
    }),

    submit2FA: (code) => post(`${BASE}/auth/2fa/authenticate`, { code }),

    beginPasskeyLogin: () => get(`${BASE}/auth/webauthn/login`),

    completePasskeyLogin: (credential) => post(`${BASE}/auth/webauthn/login`, { credential }),

    reauthenticate: (password) => post(`${BASE}/auth/reauthenticate`, { password }),
  };

export { authApi };
