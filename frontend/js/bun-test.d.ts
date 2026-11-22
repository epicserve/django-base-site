// Types for the parts of `bun:test` that the unit tests (`*.test.ts`, run by `just test_js`) use. The test runner is
// built into bun, but its types are a separate package, `@types/bun`. Add to these as tests need more.
declare module 'bun:test' {
  export function describe(label: string, fn: () => void): void;
  export function test(label: string, fn: () => void | Promise<void>): void;
  export function expect(actual: unknown): {
    toBe(expected: unknown): void;
    toEqual(expected: unknown): void;
  };
}
