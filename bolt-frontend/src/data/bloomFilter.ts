import type { BloomFilterState } from './types';

/**
 * Bloom Filter implementation.
 * Uses double hashing (h1 + i*h2) to simulate k independent hash functions.
 * All hash functions operate on string inputs and produce indices in [0, size).
 */

function hashStr(s: string, seed: number): number {
  let h = seed;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function createBloomFilter(size: number, expectedItems: number): BloomFilterState {
  const optimalHashCount = Math.max(1, Math.round((size / Math.max(1, expectedItems)) * Math.LN2));
  return {
    bitArray: new Array(size).fill(false),
    size,
    hashCount: Math.min(optimalHashCount, 10),
    insertedItems: [],
    falsePositiveRate: 0,
  };
}

export function bloomInsert(state: BloomFilterState, item: string): BloomFilterState {
  if (state.insertedItems.includes(item)) return state;
  const bits = [...state.bitArray];
  for (let i = 0; i < state.hashCount; i++) {
    const idx = hashStr(item, i * 31 + 17) % state.size;
    bits[idx] = true;
  }
  const newItems = [...state.insertedItems, item];
  const fpRate = calcFalsePositiveRate(newItems.length, state.size, state.hashCount);
  return { ...state, bitArray: bits, insertedItems: newItems, falsePositiveRate: fpRate };
}

export function bloomCheck(state: BloomFilterState, item: string): boolean {
  for (let i = 0; i < state.hashCount; i++) {
    const idx = hashStr(item, i * 31 + 17) % state.size;
    if (!state.bitArray[idx]) return false;
  }
  return true;
}

export function bloomExactCheck(state: BloomFilterState, item: string): boolean {
  return state.insertedItems.includes(item);
}

export function bloomClear(state: BloomFilterState): BloomFilterState {
  return {
    bitArray: new Array(state.size).fill(false),
    size: state.size,
    hashCount: state.hashCount,
    insertedItems: [],
    falsePositiveRate: 0,
  };
}

export function calcFalsePositiveRate(n: number, m: number, k: number): number {
  if (n === 0 || m === 0) return 0;
  return Math.pow(1 - Math.pow(1 - 1 / m, k * n), k);
}

export function evaluateFalsePositives(state: BloomFilterState, testItems: string[]): {
  total: number;
  falsePositives: number;
  truePositives: number;
  trueNegatives: number;
  falseNegatives: number;
  rate: number;
} {
  let fp = 0, tp = 0, tn = 0, fn = 0;
  for (const item of testItems) {
    const inFilter = bloomCheck(state, item);
    const actuallyInserted = bloomExactCheck(state, item);
    if (inFilter && actuallyInserted) tp++;
    else if (inFilter && !actuallyInserted) fp++;
    else if (!inFilter && actuallyInserted) fn++;
    else tn++;
  }
  const total = testItems.length;
  return { total, falsePositives: fp, truePositives: tp, trueNegatives: tn, falseNegatives: fn, rate: total > 0 ? fp / total : 0 };
}
