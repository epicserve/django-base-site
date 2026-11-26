import { describe, expect, test } from 'vitest';
import { getAllResults, type Page } from './api';

function pages<Item>(...all: Item[][]): (page: number) => Promise<Page<Item>> {
  return async (page) => ({
    results: all[page - 1] ?? [],
    next: page < all.length ? `/api/teams/?page=${page + 1}` : null,
  });
}

describe('getAllResults', () => {
  test('follows every page and keeps their order', async () => {
    const requested: number[] = [];
    const fetchPage = pages(['Sales', 'Accounting'], ['Warehouse'], ['Annex']);

    const results = await getAllResults((page) => {
      requested.push(page);
      return fetchPage(page);
    });

    expect(results).toEqual(['Sales', 'Accounting', 'Warehouse', 'Annex']);
    expect(requested).toEqual([1, 2, 3]);
  });

  test('stops after one page when there is no next page', async () => {
    const requested: number[] = [];

    const results = await getAllResults((page) => {
      requested.push(page);
      return Promise.resolve({ results: ['Sales'], next: undefined });
    });

    expect(results).toEqual(['Sales']);
    expect(requested).toEqual([1]);
  });

  test('returns nothing for an empty list', async () => {
    expect(await getAllResults(pages<string>([]))).toEqual([]);
  });
});
