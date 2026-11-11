/**
 * The SPA's API client.
 *
 * `api` is typed from the OpenAPI types that `just generate_api_types` writes to `@/api/`, so `vue-tsc` checks every
 * call's path, method, params, body, and response against the backend. Pass the path template and its params rather
 * than building the URL yourself, and wrap the call in `unwrap()` to get the response body:
 *
 *     const team = await unwrap(api.GET('/api/teams/{team_id}/', { params: { path: { team_id } } }));
 *
 * A non-2xx response throws an `ApiError`. Narrow with `instanceof` before reading it:
 *
 *     catch (err) { if (err instanceof ApiError && err.response.status === 404) ... }
 */
import createClient, { type Client, type FetchResponse, type MaybeOptionalInit, type Middleware } from 'openapi-fetch';
import type { paths as AllauthPaths } from '@/api/allauth';
import type { paths as ApiPaths } from '@/api/schema';

export type Paths = ApiPaths & AllauthPaths;

type JsonRequestBody<Op> = Op extends { requestBody?: { content: { 'application/json': infer Body } } } ? Body : never;

/** The JSON request body of a path and method, e.g. `RequestBody<'/_allauth/browser/v1/auth/signup', 'post'>`. */
export type RequestBody<P extends keyof Paths, M extends keyof Paths[P]> = JsonRequestBody<Paths[P][M]>;

/** Thrown for a non-2xx response. `data` is the parsed JSON body, or `null` when the body isn't JSON. */
export class ApiError extends Error {
  readonly response: Response;
  readonly data: unknown;

  constructor(response: Response, data: unknown) {
    super(`HTTP ${response.status}`);
    this.name = 'ApiError';
    this.response = response;
    this.data = data;
  }
}

function getCookie(name: string): string | null {
  for (const cookie of document.cookie ? document.cookie.split(';') : []) {
    const trimmed = cookie.trim();

    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }
  return null;
}

export function getCSRFToken(): string | null {
  return getCookie('csrftoken');
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

const csrfAndErrors: Middleware = {
  onRequest({ request }) {
    const token = getCSRFToken();

    if (token) request.headers.set('X-CSRFToken', token);
    return request;
  },
  async onResponse({ response }) {
    if (!response.ok) throw new ApiError(response, await readJson(response));
    return undefined;
  },
};

// openapi-fetch infers each call's options as a type parameter and allows any extra keys on them, so on its own it
// accepts a body with properties the endpoint doesn't take (c571d009 sent PATCH's `{ email, primary }` with PUT). These
// types wrap its methods with one more rule: every top-level key of an inline `body` must be in that path and method's
// request body. Nested objects aren't checked. See api.type-test.ts.
type Method = 'get' | 'put' | 'post' | 'delete' | 'patch';
type PathsWith<M extends Method> = { [P in keyof Paths]: Paths[P] extends Record<M, unknown> ? P : never }[keyof Paths];
type RequiredKeysOf<T> = { [K in keyof T]-?: Partial<Pick<T, K>> extends Pick<T, K> ? never : K }[keyof T];
type Operation<P extends keyof Paths, M extends Method> = Extract<Paths[P][M], Record<string | number, unknown>>;
type BodyOf<Op> = Op extends { requestBody?: { content: infer Content } } ? Content[keyof Content] : never;
// Every key of every member, so a union body (allauth's login takes an email, username, or phone) allows all of them.
type KeysOfUnion<T> = T extends unknown ? keyof T : never;
type NoExtraBodyKeys<Init, Op> = [Init] extends [{ body: infer Body }]
  ? [Body] extends [object]
    ? { body?: { [K in Exclude<keyof Body, KeysOfUnion<BodyOf<Op>>>]: never } }
    : unknown
  : unknown;

type StrictMethod<M extends Method> = <P extends PathsWith<M>, Init extends MaybeOptionalInit<Paths[P], M>>(
  url: P,
  ...init: RequiredKeysOf<Init> extends never
    ? [(Init & NoExtraBodyKeys<Init, Operation<P, M>>)?]
    : [Init & NoExtraBodyKeys<Init, Operation<P, M>>]
) => Promise<FetchResponse<Operation<P, M>, Init, `${string}/${string}`>>;

type StrictClient = Omit<Client<Paths>, 'GET' | 'PUT' | 'POST' | 'DELETE' | 'PATCH'> & {
  GET: StrictMethod<'get'>;
  PUT: StrictMethod<'put'>;
  POST: StrictMethod<'post'>;
  DELETE: StrictMethod<'delete'>;
  PATCH: StrictMethod<'patch'>;
};

export const api = createClient<Paths>() as StrictClient;
api.use(csrfAndErrors);

/**
 * Resolve an `api` call to its response body: the parsed JSON, or `undefined` for a response with no body (204).
 * Non-2xx responses never get here, because `api` throws an `ApiError` for them.
 */
export async function unwrap<Data>(
  call: Promise<{ data?: Data; response: Response }>,
): Promise<[Data] extends [never] ? undefined : Data> {
  const { data } = await call;

  return data as [Data] extends [never] ? undefined : Data;
}

/**
 * A `bodySerializer` for multipart endpoints such as file uploads. The body is still typed from the spec; this sends
 * it as `FormData`, leaving out `undefined` fields:
 *
 *     api.POST('/api/avatar/', { body: { image: file }, bodySerializer: formDataBody })
 */
export function formDataBody(body: Record<string, string | Blob | undefined>): FormData {
  const formData = new FormData();

  for (const [key, value] of Object.entries(body)) {
    if (value !== undefined) formData.append(key, value);
  }
  return formData;
}

// ---------------------------------------------------------------------------------------------------------------------
// Untyped helpers, kept for the files that haven't been converted to TypeScript yet. New code uses `api` instead.
// ---------------------------------------------------------------------------------------------------------------------

type QueryParams = Record<string, string | number | boolean | null | undefined | (string | number)[]>;

async function request(url: string, options: RequestInit = {}): Promise<unknown> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken() ?? '',
      ...options.headers,
    },
  });

  if (!response.ok) throw new ApiError(response, await readJson(response));
  if (response.status === 204) return null;
  return response.json();
}

/** @deprecated Untyped. Use `api.GET()` with `unwrap()`. */
export function get(url: string, params: QueryParams = {}): Promise<unknown> {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      value.forEach((v) => searchParams.append(key, String(v)));
    } else if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, String(value));
    }
  }
  const qs = searchParams.toString();

  return request(qs ? `${url}?${qs}` : url, { method: 'GET' });
}

/** @deprecated Untyped. Use `api.POST()` with `unwrap()`. */
export function post(url: string, data?: unknown): Promise<unknown> {
  return request(url, { method: 'POST', body: JSON.stringify(data) });
}

/** @deprecated Untyped. Use `api.PATCH()` with `unwrap()`. */
export function patch(url: string, data?: unknown): Promise<unknown> {
  return request(url, { method: 'PATCH', body: JSON.stringify(data) });
}

/** @deprecated Untyped. Use `api.PUT()` with `unwrap()`. */
export function put(url: string, data?: unknown): Promise<unknown> {
  return request(url, { method: 'PUT', body: JSON.stringify(data) });
}

/** @deprecated Untyped. Use `api.DELETE()` with `unwrap()`. */
export function del(url: string): Promise<unknown> {
  return request(url, { method: 'DELETE' });
}

/** Turn a ninja error body into `{ field: [messages] }`, for form fields to show. */
export function parseErrors(error: unknown): Record<string, string[]> {
  const data = error instanceof ApiError ? error.data : null;

  if (data && typeof data === 'object') {
    const errors: Record<string, string[]> = {};

    for (const [key, value] of Object.entries(data)) {
      errors[key] = Array.isArray(value) ? value : [value];
    }
    return errors;
  }
  return { non_field_errors: ['An unexpected error occurred.'] };
}

/** @deprecated Untyped. Fetches every page of a paginated list. */
export async function getAllResults(
  url: string,
  params: QueryParams = {},
  results: unknown[] = [],
): Promise<unknown[]> {
  const data = (await get(url, params)) as { results: unknown[]; next: string | null };

  results.push(...data.results);
  if (data.next) {
    const nextUrl = new URL(data.next),
      nextParams = { ...params, page: nextUrl.searchParams.get('page') };

    return getAllResults(url, nextParams, results);
  }
  return results;
}
