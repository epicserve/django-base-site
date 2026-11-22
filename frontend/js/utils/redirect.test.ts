import { describe, expect, test } from 'bun:test';
import { safeNextUrl } from './redirect';

describe('safeNextUrl', () => {
  for (const next of ['/', '/notifications/', '/organizations/dunder-mifflin/settings/teams/?page=2#sales']) {
    test(`keeps the path ${JSON.stringify(next)}`, () => {
      expect(safeNextUrl(next)).toBe(next);
    });
  }

  // A query parameter given twice, such as `?next=/a&next=/b`, is an array.
  for (const next of [undefined, null, 42, ['/notifications/'], '']) {
    test(`falls back when next is ${JSON.stringify(next)}`, () => {
      expect(safeNextUrl(next)).toBe('/');
    });
  }

  for (const next of ['https://evil.example/', 'javascript:alert(1)', 'evil.example', 'notifications/', ' /']) {
    test(`rejects ${JSON.stringify(next)}, which isn't a path`, () => {
      expect(safeNextUrl(next)).toBe('/');
    });
  }

  // Browsers read each of these as another site's address.
  for (const next of ['//evil.example', '//evil.example/notifications/', '/\\evil.example', '\\\\evil.example']) {
    test(`rejects ${JSON.stringify(next)}, which leads to another site`, () => {
      expect(safeNextUrl(next)).toBe('/');
    });
  }

  test('returns the fallback it is given', () => {
    expect(safeNextUrl('//evil.example', '/accounts/security/')).toBe('/accounts/security/');
  });

  test('rejects /accounts/ pages unless they are allowed', () => {
    expect(safeNextUrl('/accounts/email/')).toBe('/');
    expect(safeNextUrl('/accounts/email/', '/', { allowAccounts: true })).toBe('/accounts/email/');
  });
});
