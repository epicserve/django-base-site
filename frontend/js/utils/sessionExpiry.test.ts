import { describe, expect, test } from 'bun:test';
import { sessionEnded, signInAgainUrl } from './sessionExpiry';

describe('sessionEnded', () => {
  for (const url of ['/api/teams/', 'http://localhost:8000/api/notifications/?page=2']) {
    test(`a 401 from ${JSON.stringify(url)} while signed in ends the session`, () => {
      expect(sessionEnded(url, true)).toBe(true);
    });
  }

  test('a 401 while signed out ends nothing', () => {
    expect(sessionEnded('/api/invite-by-key/abc/accept/', false)).toBe(false);
  });

  // allauth answers 401 while a two-factor code is pending and after signing out.
  for (const url of ['/_allauth/browser/v1/auth/login', 'http://localhost:8000/_allauth/browser/v1/auth/session']) {
    test(`a 401 from ${JSON.stringify(url)} isn't the session ending`, () => {
      expect(sessionEnded(url, true)).toBe(false);
    });
  }

  test('only a path that starts with /api/ counts', () => {
    expect(sessionEnded('/apiary/', true)).toBe(false);
    expect(sessionEnded('/notifications/?from=/api/', true)).toBe(false);
  });
});

describe('signInAgainUrl', () => {
  test('comes back to the page, query and all', () => {
    expect(signInAgainUrl('/organizations/dunder-mifflin/settings/teams/?page=2')).toBe(
      '/accounts/login/?next=%2Forganizations%2Fdunder-mifflin%2Fsettings%2Fteams%2F%3Fpage%3D2&session=expired',
    );
  });
});
