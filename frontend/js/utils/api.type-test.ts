/**
 * Type-level regression tests for the API client, checked by `vue-tsc` in `just lint`. Nothing imports this file, so
 * it never runs or ships.
 *
 * Each `@ts-expect-error` line is a bug that shipped before the API was typed. If the types stop rejecting it, the
 * directive goes unused and `vue-tsc` fails. The lines around it are the same calls written correctly, which must
 * type-check, so a directive can't pass on an unrelated error such as a path that no longer exists.
 */
import { api, ApiError, unwrap } from '@/utils/api';
import { userFullName } from '@/utils/format';

declare const email: string;

// c571d009: the SPA marked an email as primary with PUT, which allauth treats as "resend the verification email".
// TypeScript only checks for unknown properties on an inline object literal, so keep these bodies inline.
export function markEmailAsPrimary() {
  void api.PATCH('/_allauth/browser/v1/account/email', { body: { email, primary: true } });
  void api.PUT('/_allauth/browser/v1/account/email', { body: { email } });
  // @ts-expect-error PUT's body is `{ email }`; `primary` belongs to PATCH.
  void api.PUT('/_allauth/browser/v1/account/email', { body: { email, primary: true } });
}

// f3a484a1: AcceptInviteView read `err.status`, which is always undefined, so its 404 message never showed.
export function readErrorStatus(err: unknown) {
  if (err instanceof ApiError) {
    void err.response.status;
    // @ts-expect-error The status is on `err.response`; ApiError has no `status`.
    void err.status;
  }
  // @ts-expect-error A caught error is `unknown` until it's narrowed with `instanceof ApiError`.
  void err.response;
}

// A request body can leave out a field the backend gives a default (TeamIn's `members`), but not a required one.
// openapi-typescript makes every field with a default required unless generate-api-types.mjs relaxes it.
export function leaveOutDefaultedFields(credential: Record<string, unknown>) {
  void api.POST('/api/teams/', { body: { name: 'Sales' } });
  // @ts-expect-error TeamIn's `name` has no default.
  void api.POST('/api/teams/', { body: { members: [] } });

  // allauth's spec types a WebAuthn credential as an object without listing its properties, which means any object.
  void api.POST('/_allauth/browser/v1/auth/webauthn/login', { body: { credential } });
}

// The notification bell and archive named the actor with userFullName(), which reads first and last names. An actor
// only has `full_name` and `username`, so they showed the username.
export async function nameNotificationActor() {
  const { results } = await unwrap(api.GET('/api/notifications/'));
  const actor = results[0]?.actor;
  if (actor) {
    void actor.full_name;
    // @ts-expect-error NotificationActorOut has no first or last name; use `full_name`.
    void userFullName(actor);
  }
}

// Responses are typed from the backend's schemas. If they came back as `any`, nothing above would catch a removed or
// renamed field.
export async function readResponses() {
  const context = await unwrap(api.GET('/api/app-context/'));
  const siteName: string = context.siteName;
  // @ts-expect-error `siteName` is a string.
  const count: number = context.siteName;
  // @ts-expect-error app-context has no `site_name`; a typo or a renamed field fails here.
  void context.site_name;

  // A response with no body (204) resolves to `undefined`.
  const nothing: undefined = await unwrap(api.DELETE('/api/avatar/'));

  return { siteName, count, nothing };
}
