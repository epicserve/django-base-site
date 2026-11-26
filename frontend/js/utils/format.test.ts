import { describe, expect, test } from 'vitest';
import { sentencePeriod } from './format';

describe('sentencePeriod', () => {
  test('ends a sentence that ends in a name', () => {
    expect(sentencePeriod('Dunder Mifflin')).toBe('.');
  });

  test("doesn't add a second period to a name that ends in one", () => {
    // "Dunder Mifflin Inc." used to end the invitation's sentence with "Inc..".
    expect(sentencePeriod('Dunder Mifflin Inc.')).toBe('');
  });

  for (const text of [null, undefined]) {
    test(`ends the sentence when the name is ${text}`, () => {
      expect(sentencePeriod(text)).toBe('.');
    });
  }
});
