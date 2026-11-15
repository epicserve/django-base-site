import { api, unwrap, type RequestBody } from '@/utils/api';

type AllauthError = { param?: string; message: string };

export function parseAllauthErrors(responseData: unknown): Record<string, string[]> {
  const errors: Record<string, string[]> = {};
  const list =
    responseData && typeof responseData === 'object' && 'errors' in responseData && Array.isArray(responseData.errors)
      ? (responseData.errors as AllauthError[])
      : [];

  for (const err of list) {
    const key = err.param || 'non_field_errors';

    (errors[key] ??= []).push(err.message);
  }
  if (Object.keys(errors).length === 0) {
    return { non_field_errors: ['An unexpected error occurred.'] };
  }
  return errors;
}

type WebAuthnCredential = RequestBody<'/_allauth/browser/v1/auth/webauthn/login', 'post'>['credential'];
type AuthenticatorId = RequestBody<
  '/_allauth/browser/v1/account/authenticators/webauthn',
  'delete'
>['authenticators'][number];

const authApi = {
  getSession: () => unwrap(api.GET('/_allauth/browser/v1/auth/session')),

  login: (email: string, password: string) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/login', { body: { email, password } })),

  logout: () => unwrap(api.DELETE('/_allauth/browser/v1/auth/session')),

  signup: (data: RequestBody<'/_allauth/browser/v1/auth/signup', 'post'>) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/signup', { body: data })),

  requestPasswordReset: (email: string) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/password/request', { body: { email } })),

  resetPassword: (key: string, password: string) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/password/reset', { body: { key, password } })),

  changePassword: (data: RequestBody<'/_allauth/browser/v1/account/password/change', 'post'>) =>
    unwrap(api.POST('/_allauth/browser/v1/account/password/change', { body: data })),

  verifyEmail: (key: string) => unwrap(api.POST('/_allauth/browser/v1/auth/email/verify', { body: { key } })),

  listEmails: () => unwrap(api.GET('/_allauth/browser/v1/account/email')),

  addEmail: (email: string) => unwrap(api.POST('/_allauth/browser/v1/account/email', { body: { email } })),

  setPrimaryEmail: (email: string) =>
    unwrap(api.PATCH('/_allauth/browser/v1/account/email', { body: { email, primary: true } })),

  removeEmail: (email: string) => unwrap(api.DELETE('/_allauth/browser/v1/account/email', { body: { email } })),

  resendVerification: (email: string) => unwrap(api.PUT('/_allauth/browser/v1/account/email', { body: { email } })),

  // MFA / 2FA
  listAuthenticators: () => unwrap(api.GET('/_allauth/browser/v1/account/authenticators')),

  getTotpStatus: () => unwrap(api.GET('/_allauth/browser/v1/account/authenticators/totp')),

  activateTotp: (code: string) =>
    unwrap(api.POST('/_allauth/browser/v1/account/authenticators/totp', { body: { code } })),

  deactivateTotp: () => unwrap(api.DELETE('/_allauth/browser/v1/account/authenticators/totp')),

  listRecoveryCodes: () => unwrap(api.GET('/_allauth/browser/v1/account/authenticators/recovery-codes')),

  regenerateRecoveryCodes: () => unwrap(api.POST('/_allauth/browser/v1/account/authenticators/recovery-codes')),

  beginAddPasskey: (passwordless: boolean) =>
    unwrap(api.GET('/_allauth/browser/v1/account/authenticators/webauthn', { params: { query: { passwordless } } })),

  addPasskey: (name: string, credential: WebAuthnCredential) =>
    unwrap(api.POST('/_allauth/browser/v1/account/authenticators/webauthn', { body: { name, credential } })),

  renamePasskey: (id: AuthenticatorId, name: string) =>
    unwrap(api.PUT('/_allauth/browser/v1/account/authenticators/webauthn', { body: { id, name } })),

  removePasskey: (id: AuthenticatorId) =>
    unwrap(api.DELETE('/_allauth/browser/v1/account/authenticators/webauthn', { body: { authenticators: [id] } })),

  submit2FA: (code: string) => unwrap(api.POST('/_allauth/browser/v1/auth/2fa/authenticate', { body: { code } })),

  beginPasskeyLogin: () => unwrap(api.GET('/_allauth/browser/v1/auth/webauthn/login')),

  completePasskeyLogin: (credential: WebAuthnCredential) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/webauthn/login', { body: { credential } })),

  reauthenticate: (password: string) =>
    unwrap(api.POST('/_allauth/browser/v1/auth/reauthenticate', { body: { password } })),
};

export { authApi };
