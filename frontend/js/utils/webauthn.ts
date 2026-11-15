/**
 * WebAuthn helpers for translating between the JSON shapes that
 * django-allauth's headless API returns and the ArrayBuffer-based
 * structures the browser's `navigator.credentials` API expects.
 *
 * allauth returns and accepts base64url-encoded strings everywhere a
 * binary value would normally appear (challenge, user.id, allowCredentials[].id,
 * response.* fields, etc.). The browser API needs ArrayBuffers.
 */

type Base64Url = string;
type DescriptorJSON = Omit<PublicKeyCredentialDescriptor, 'id'> & { id: Base64Url };
type CreationOptionsJSON = Omit<PublicKeyCredentialCreationOptions, 'challenge' | 'user' | 'excludeCredentials'> & {
  challenge: Base64Url;
  user: Omit<PublicKeyCredentialUserEntity, 'id'> & { id: Base64Url };
  excludeCredentials?: DescriptorJSON[];
};
type RequestOptionsJSON = Omit<PublicKeyCredentialRequestOptions, 'challenge' | 'allowCredentials'> & {
  challenge: Base64Url;
  allowCredentials?: DescriptorJSON[];
};

/** A credential as allauth takes it: every binary field base64url-encoded. */
export type EncodedCredential = {
  id: string;
  rawId: Base64Url;
  type: string;
  authenticatorAttachment: string | null;
  clientExtensionResults: AuthenticationExtensionsClientOutputs;
  response:
    | { clientDataJSON: Base64Url; attestationObject: Base64Url; transports?: string[] }
    | { clientDataJSON: Base64Url; authenticatorData: Base64Url; signature: Base64Url; userHandle: Base64Url | null };
};

function base64UrlToBuffer(value: Base64Url): ArrayBuffer {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/'),
    pad = padded.length % 4 === 0 ? '' : '='.repeat(4 - (padded.length % 4)),
    binary = atob(padded + pad),
    bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function bufferToBase64Url(buffer: ArrayBuffer): Base64Url {
  const bytes = new Uint8Array(buffer);
  let binary = '';

  for (let i = 0; i < bytes.byteLength; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// allauth (via fido2) wraps options in `{publicKey: {...}}`. Earlier versions
// or alternate setups returned the inner object directly, so unwrap defensively.
// allauth's spec types the options as plain objects, so this is where they take
// WebAuthn's JSON shapes.
function unwrap<Options>(options: Record<string, unknown>): Options {
  return (options.publicKey ?? options) as Options;
}

export function decodeCreationOptions(options: Record<string, unknown>): PublicKeyCredentialCreationOptions {
  const inner = unwrap<CreationOptionsJSON>(options);

  return {
    ...inner,
    challenge: base64UrlToBuffer(inner.challenge),
    user: { ...inner.user, id: base64UrlToBuffer(inner.user.id) },
    excludeCredentials: inner.excludeCredentials?.map((c) => ({ ...c, id: base64UrlToBuffer(c.id) })),
  };
}

export function decodeRequestOptions(options: Record<string, unknown>): PublicKeyCredentialRequestOptions {
  const inner = unwrap<RequestOptionsJSON>(options);

  return {
    ...inner,
    challenge: base64UrlToBuffer(inner.challenge),
    allowCredentials: inner.allowCredentials?.map((c) => ({ ...c, id: base64UrlToBuffer(c.id) })),
  };
}

export function encodeCredential(credential: Credential | null): EncodedCredential {
  if (!(credential instanceof PublicKeyCredential)) throw new Error('The browser returned no passkey.');
  const { response } = credential,
    base = {
      id: credential.id,
      rawId: bufferToBase64Url(credential.rawId),
      type: credential.type,
      authenticatorAttachment: credential.authenticatorAttachment ?? null,
      clientExtensionResults: credential.getClientExtensionResults?.() ?? {},
    };

  if (response instanceof AuthenticatorAttestationResponse) {
    // Registration response
    return {
      ...base,
      response: {
        clientDataJSON: bufferToBase64Url(response.clientDataJSON),
        attestationObject: bufferToBase64Url(response.attestationObject),
        ...(response.getTransports ? { transports: response.getTransports() } : {}),
      },
    };
  }
  if (response instanceof AuthenticatorAssertionResponse) {
    // Assertion response
    return {
      ...base,
      response: {
        clientDataJSON: bufferToBase64Url(response.clientDataJSON),
        authenticatorData: bufferToBase64Url(response.authenticatorData),
        signature: bufferToBase64Url(response.signature),
        userHandle: response.userHandle ? bufferToBase64Url(response.userHandle) : null,
      },
    };
  }
  throw new Error('The browser returned an unknown kind of passkey response.');
}

export async function createPasskeyCredential(
  creationOptionsJson: Record<string, unknown>,
): Promise<EncodedCredential> {
  const publicKey = decodeCreationOptions(creationOptionsJson),
    credential = await navigator.credentials.create({ publicKey });

  return encodeCredential(credential);
}

// `mediation: 'conditional'` offers passkeys in the autofill list of an input with
// `autocomplete="... webauthn"` instead of opening the browser's modal passkey dialog.
// Pass an AbortSignal to cancel a pending request (only one can be in flight at a time).
export async function getPasskeyAssertion(
  requestOptionsJson: Record<string, unknown>,
  { mediation, signal }: { mediation?: CredentialMediationRequirement; signal?: AbortSignal } = {},
): Promise<EncodedCredential> {
  const publicKey = decodeRequestOptions(requestOptionsJson),
    credential = await navigator.credentials.get({ publicKey, mediation, signal });

  return encodeCredential(credential);
}

export function isWebAuthnSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.PublicKeyCredential !== 'undefined' &&
    typeof navigator.credentials?.create === 'function' &&
    typeof navigator.credentials?.get === 'function'
  );
}

export async function isConditionalMediationAvailable(): Promise<boolean> {
  if (!isWebAuthnSupported() || typeof PublicKeyCredential.isConditionalMediationAvailable !== 'function') {
    return false;
  }
  try {
    return await PublicKeyCredential.isConditionalMediationAvailable();
  } catch {
    return false;
  }
}
