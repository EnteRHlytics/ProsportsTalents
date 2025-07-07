import { describe, expect, it } from 'vitest';
import { computeSeasonData } from '../src/utils/stats.js';

const summary = {
  '2022': { points: '10', rebounds: '5' },
  '2023': { points: '15', rebounds: '7' }
};

describe('computeSeasonData', () => {
  it('computes seasons, columns and highs', () => {
    const result = computeSeasonData(summary);
    expect(result.seasons).toEqual(['2022', '2023']);
    expect(result.columns).toEqual(['points', 'rebounds']);
    expect(result.highs.points).toBe(15);
    expect(result.highs.rebounds).toBe(7);
  });
});
