import type { DgimState, DgimBucket } from './types';

/**
 * Datar-Gionis-Indyk-Motwani (DGIM) algorithm for counting 1s in a sliding window
 * using O(log^2 N) space. Each bucket covers a power-of-two number of 1-bits.
 * We maintain at most 2 buckets of each size (allowing temporary 3 before merging).
 */

export function createDgim(windowSize: number): DgimState {
  return {
    buckets: [],
    windowSize,
    currentTimestamp: 0,
    approximateCount: 0,
    exactCount: 0,
    errorRate: 0,
  };
}

export function dgimAddBit(state: DgimState, bit: 0 | 1): DgimState {
  const ts = state.currentTimestamp + 1;
  let buckets = bit === 1 ? [{ timestamp: ts, size: 1 }, ...state.buckets] : [...state.buckets];

  // Remove expired buckets (outside the window)
  const cutoff = ts - state.windowSize;
  buckets = buckets.filter((b) => b.timestamp > cutoff);

  // Merge if 3 buckets of the same size exist
  let i = buckets.length - 1;
  while (i >= 2) {
    if (buckets[i].size === buckets[i - 1].size && buckets[i - 1].size === buckets[i - 2].size) {
      const merged: DgimBucket = {
        timestamp: buckets[i - 1].timestamp,
        size: buckets[i - 2].size * 2,
      };
      buckets = [...buckets.slice(0, i - 2), merged, ...buckets.slice(i)];
      i = buckets.length - 1;
    } else {
      i--;
    }
  }

  const approx = dgimApproxCount({ ...state, buckets, currentTimestamp: ts });
  return { buckets, windowSize: state.windowSize, currentTimestamp: ts, approximateCount: approx, exactCount: 0, errorRate: 0 };
}

export function dgimApproxCount(state: DgimState): number {
  if (state.buckets.length === 0) return 0;
  const cutoff = state.currentTimestamp - state.windowSize;
  const active = state.buckets.filter((b) => b.timestamp > cutoff);
  if (active.length === 0) return 0;

  // Sum all but the last bucket fully, add half of the last
  let sum = 0;
  for (let i = 0; i < active.length - 1; i++) {
    sum += active[i].size;
  }
  sum += Math.ceil(active[active.length - 1].size / 2);
  return sum;
}

export function dgimExactCount(bits: number[], windowSize: number): number {
  const start = Math.max(0, bits.length - windowSize);
  return bits.slice(start).filter((b) => b === 1).length;
}

export function dgimProcessStream(bits: (0 | 1)[], windowSize: number): {
  state: DgimState;
  exactBits: number[];
  exactCounts: number[];
  approxCounts: number[];
  errors: number[];
} {
  let state = createDgim(windowSize);
  const exactBits: number[] = [];
  const exactCounts: number[] = [];
  const approxCounts: number[] = [];
  const errors: number[] = [];

  for (const bit of bits) {
    state = dgimAddBit(state, bit);
    exactBits.push(bit);
    const exact = dgimExactCount(exactBits, windowSize);
    const approx = dgimApproxCount(state);
    exactCounts.push(exact);
    approxCounts.push(approx);
    errors.push(exact > 0 ? Math.abs(approx - exact) / exact : 0);
  }

  return { state: { ...state, exactCount: exactCounts[exactCounts.length - 1] ?? 0, errorRate: errors[errors.length - 1] ?? 0 }, exactBits, exactCounts, approxCounts, errors };
}

export function generateRandomStream(length: number, probability: number): (0 | 1)[] {
  const bits: (0 | 1)[] = [];
  for (let i = 0; i < length; i++) {
    bits.push(Math.random() < probability ? 1 : 0);
  }
  return bits;
}
