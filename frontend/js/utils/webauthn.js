/**
 * WebAuthn helpers for translating between the JSON shapes that
 * django-allauth's headless API returns and the ArrayBuffer-based
 * structures the browser's `navigator.credentials` API expects.
 *
 * allauth returns and accepts base64url-encoded strings everywhere a
 * binary value would normally appear (challenge, user.id, allowCredentials[].id,
 * response.* fields, etc.). The browser API needs ArrayBuffers.
 */

function base64UrlToBuffer(value) {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/');
  const pad = padded.length % 4 === 0 ? '' : '='.repeat(4 - (padded.length % 4));
  const binary = atob(padded + pad);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function bufferToBase64Url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';

  for (let i = 0; i < bytes.byteLength; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// allauth (via fido2) wraps options in `{publicKey: {...}}`. Earlier versions
// or alternate setups returned the inner object directly, so unwrap defensively.
function unwrap(options) {
  return options?.publicKey ?? options;
}

export function decodeCreationOptions(options) {
  const inner = unwrap(options);
  const decoded = { ...inner, challenge: base64UrlToBuffer(inner.challenge) };

  if (inner.user) {
    decoded.user = { ...inner.user, id: base64UrlToBuffer(inner.user.id) };
  }
  if (inner.excludeCredentials) {
    decoded.excludeCredentials = inner.excludeCredentials.map((c) => ({
      ...c,
      id: base64UrlToBuffer(c.id),
    }));
  }
  return decoded;
}

export function decodeRequestOptions(options) {
  const inner = unwrap(options);
  const decoded = { ...inner, challenge: base64UrlToBuffer(inner.challenge) };

  if (inner.allowCredentials) {
    decoded.allowCredentials = inner.allowCredentials.map((c) => ({
      ...c,
      id: base64UrlToBuffer(c.id),
    }));
  }
  return decoded;
}

export function encodeCredential(credential) {
  const { response } = credential;
  const encoded = {
    id: credential.id,
    rawId: bufferToBase64Url(credential.rawId),
    type: credential.type,
    authenticatorAttachment: credential.authenticatorAttachment ?? null,
    clientExtensionResults: credential.getClientExtensionResults?.() ?? {},
    response: {},
  };

  if (response.attestationObject !== undefined) {
    // Registration response (PublicKeyCredentialAttestationResponse)
    encoded.response = {
      clientDataJSON: bufferToBase64Url(response.clientDataJSON),
      attestationObject: bufferToBase64Url(response.attestationObject),
    };
    if (response.getTransports) encoded.response.transports = response.getTransports();
  } else {
    // Assertion response (PublicKeyCredentialAssertionResponse)
    encoded.response = {
      clientDataJSON: bufferToBase64Url(response.clientDataJSON),
      authenticatorData: bufferToBase64Url(response.authenticatorData),
      signature: bufferToBase64Url(response.signature),
      userHandle: response.userHandle ? bufferToBase64Url(response.userHandle) : null,
    };
  }
  return encoded;
}

export async function createPasskeyCredential(creationOptionsJson) {
  const publicKey = decodeCreationOptions(creationOptionsJson);
  const credential = await navigator.credentials.create({ publicKey });

  return encodeCredential(credential);
}

export async function getPasskeyAssertion(requestOptionsJson) {
  const publicKey = decodeRequestOptions(requestOptionsJson);
  const credential = await navigator.credentials.get({ publicKey });

  return encodeCredential(credential);
}

export function isWebAuthnSupported() {
  return (
    typeof window !== 'undefined' &&
    typeof window.PublicKeyCredential !== 'undefined' &&
    typeof navigator.credentials?.create === 'function' &&
    typeof navigator.credentials?.get === 'function'
  );
}
